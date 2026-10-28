"""Test-only crash barriers around the production workflow's dummy steps."""

import json
import os
from pathlib import Path
from threading import Event
from urllib.request import Request, urlopen

from dbos import DBOS, DBOSConfig, DBOSPortableJSONSerializer

from agora_worker import workflows
from agora_worker.config import Settings

point = os.environ["RECOVERY_POINT"]
server = os.environ["RECOVERY_SERVER"]


def call(path: str) -> None:
    request = Request(
        server + path,
        data=json.dumps({"key": f"{DBOS.workflow_id}:add"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=30) as response:
        response.read()


@DBOS.step(name="recovery.add", retries_allowed=True, interval_seconds=0.05, max_attempts=3)
def durable_add(left: int, right: int) -> int:
    if point == "during-step":
        call("/gate")
    call("/effect")
    if point == "effect-gap":
        call("/gate")
    return left + right


def add(left: int, right: int) -> int:
    if point == "before-step":
        call("/gate")
    return durable_add(left, right)


@DBOS.step(name="recovery.double")
def durable_double(value: int) -> int:
    return value * 2


def double(value: int) -> int:
    if point == "after-step":
        call("/gate")
    return durable_double(value)


workflows.add = add
workflows.double = double
settings = Settings()
config: DBOSConfig = {
    "name": "agora-worker",
    "system_database_url": settings.dbos_database_url,
    "dbos_system_schema": settings.dbos_system_schema,
    "executor_id": "agora-recovery-test",
    "application_version": "recovery-v1",
    "run_admin_server": False,
    "enable_otlp": False,
    "serializer": DBOSPortableJSONSerializer(),
}
DBOS(config=config)
DBOS.launch()
DBOS.register_queue(workflows.QUEUE_NAME, worker_concurrency=1)
Path(os.environ["RECOVERY_READY"]).touch()
Event().wait()
