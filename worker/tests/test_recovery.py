"""SIGKILL real worker processes; keep effects and PostgreSQL outside them."""

import json
import os
import socket
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Event, Lock, Thread
from time import monotonic, sleep
from typing import Any
from urllib.request import Request, urlopen
from uuid import uuid4

import psycopg
import pytest
from dbos import DBOSClient, DBOSPortableJSONSerializer
from psycopg import sql

from agora_worker.config import Settings

pytestmark = [pytest.mark.integration, pytest.mark.recovery]


@dataclass
class Effects:
    idempotent: bool
    retry: bool
    calls: int = 0
    effects: int = 0
    duplicates: int = 0
    keys: set[str] = field(default_factory=lambda: set[str]())
    hit: Event = field(default_factory=Event)
    release: Event = field(default_factory=Event)
    lock: Lock = field(default_factory=Lock)


def handler_for(state: Effects) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            pass

        def do_POST(self) -> None:
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            code = 200
            if self.path == "/gate":
                with state.lock:
                    block = not state.hit.is_set()
                    state.hit.set()
                if block:
                    state.release.wait(timeout=30)
            else:
                with state.lock:
                    state.calls += 1
                    if state.retry and state.calls == 1:
                        code = 503
                    else:
                        duplicate = payload["key"] in state.keys
                        state.duplicates += int(duplicate)
                        if not state.idempotent or not duplicate:
                            state.effects += 1
                        state.keys.add(payload["key"])
            self.send_response(code)
            self.end_headers()

    return Handler


def wait_for(predicate: Callable[[], bool], description: str) -> None:
    deadline = monotonic() + 20
    while monotonic() < deadline:
        if predicate():
            return
        sleep(0.05)
    pytest.fail(f"Timed out: {description}")


def http(base: str, path: str, body: object = None) -> dict[str, Any]:
    request = Request(
        base + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=3) as response:
        return json.load(response)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.mark.parametrize(
    ("point", "idempotent", "expected_calls", "expected_effects", "saved_before"),
    [
        ("before-step", True, 1, 1, 0),
        ("during-step", True, 1, 1, 0),
        ("after-step", True, 1, 1, 1),
        ("effect-gap", True, 2, 1, 0),
        ("effect-gap", False, 2, 2, 0),
        ("retry", True, 2, 1, 0),
    ],
)
def test_recovery(
    tmp_path: Path,
    point: str,
    idempotent: bool,
    expected_calls: int,
    expected_effects: int,
    saved_before: int,
) -> None:
    if not os.environ.get("POSTGRES_PASSWORD"):
        pytest.fail("POSTGRES_PASSWORD is required for recovery tests", pytrace=False)
    schema = f"recovery_{uuid4().hex}"
    env = {**os.environ, "DBOS_SYSTEM_SCHEMA": schema}
    state = Effects(idempotent=idempotent, retry=point == "retry")
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(state))
    server.daemon_threads = True
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    ready = tmp_path / "ready"
    env.update(
        RECOVERY_POINT=point,
        RECOVERY_SERVER=f"http://127.0.0.1:{server.server_port}",
        RECOVERY_READY=str(ready),
    )
    worker_script = Path(__file__).parent / "fixtures" / "recovery_worker.py"
    processes: list[subprocess.Popen[bytes]] = []
    client: DBOSClient | None = None

    def start_worker() -> subprocess.Popen[bytes]:
        ready.unlink(missing_ok=True)
        process = subprocess.Popen(
            [sys.executable, str(worker_script)],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        processes.append(process)
        wait_for(lambda: ready.exists() or process.poll() is not None, "worker startup")
        assert process.poll() is None, "Recovery worker failed to start"
        return process

    try:
        worker = start_worker()
        client = DBOSClient(
            system_database_url=Settings().dbos_database_url,
            dbos_system_schema=schema,
            application_name="agora-worker",
            serializer=DBOSPortableJSONSerializer(),
            retry_connection_errors=False,
        )
        port = free_port()
        base = f"http://127.0.0.1:{port}"
        api = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "agora_api.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        processes.append(api)

        def api_ready() -> bool:
            assert api.poll() is None, "Recovery API failed to start"
            try:
                return http(base, "/health")["status"] == "ok"
            except OSError:
                return False

        wait_for(api_ready, "API startup")
        request = {
            "operation": "add_then_scale",
            "inputs": {"left": 2, "right": 3, "double_positive": True},
        }
        workflow_id = http(base, "/workflows", request)["id"]
        path = f"/workflows/{workflow_id}"
        if point != "retry":
            assert state.hit.wait(timeout=20), "Worker did not reach crash barrier"
            assert http(base, path)["status"] == "running"
            steps = client.list_workflow_steps(workflow_id)
            assert len(steps) == saved_before
            if saved_before:
                assert steps[0]["output"] == 5
            worker.kill()
            worker.wait(timeout=5)
            state.release.set()
            start_worker()
        wait_for(lambda: http(base, path)["status"] == "successful", "recovered workflow")
        result = http(base, path)
        assert result["result"] == {"value": 10.0, "branch": "doubled"}
        assert result["request"] == request
        steps = client.list_workflow_steps(workflow_id)
        assert [step["output"] for step in steps] == [5, 10]
        assert state.calls == expected_calls
        assert state.effects == expected_effects
        assert state.duplicates == int(point == "effect-gap")
        print(
            f"{point}, idempotent={idempotent}: saved={saved_before}, "
            f"calls={state.calls}, effects={state.effects}, duplicates={state.duplicates}"
        )
    finally:
        state.release.set()
        for process in reversed(processes):
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
        if client is not None:
            client.destroy()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        with psycopg.connect(str(Settings().database_url)) as connection:
            connection.execute(
                sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema))
            )
