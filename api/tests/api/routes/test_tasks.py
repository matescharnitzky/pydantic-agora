from unittest.mock import Mock
from uuid import uuid4

import psycopg
import pytest
from dbos import DBOSClient, WorkflowStatus
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agora_api.api.deps import get_database_connection, get_worker_client
from agora_api.services.runs import APPLICATION_NAME, WORKFLOW_NAME, get_run


@pytest.fixture
def registry(app: FastAPI) -> Mock:
    connection = Mock()
    connection.execute.return_value.fetchone.return_value = (
        [
            {
                "id": "new-worker-task",
                "description": "Registered by the worker without API changes",
                "input_schema": {
                    "type": "object",
                    "properties": {"text": {"type": "string", "minLength": 1}},
                    "required": ["text"],
                    "additionalProperties": False,
                },
                "output_schema": {"type": "object"},
            }
        ],
    )
    app.dependency_overrides[get_database_connection] = lambda: connection
    return connection


def test_discovery_reads_worker_metadata(app: FastAPI, registry: Mock) -> None:
    response = TestClient(app).get("/tasks")
    assert response.status_code == 200
    assert response.json() == registry.execute.return_value.fetchone.return_value[0]


def test_new_worker_task_is_enqueued_without_api_changes(app: FastAPI, registry: Mock) -> None:
    client = Mock(spec=DBOSClient)
    app.dependency_overrides[get_worker_client] = lambda: client
    payload = {"task": "new-worker-task", "inputs": {"text": "Hello"}}
    response = TestClient(app).post(
        f"/tasks/{payload['task']}/runs", json={"inputs": payload["inputs"]}
    )
    assert response.status_code == 202
    assert client.enqueue.call_args.args[1] == payload


def test_task_inputs_are_left_for_worker_validation(app: FastAPI, registry: Mock) -> None:
    client = Mock(spec=DBOSClient)
    app.dependency_overrides[get_worker_client] = lambda: client
    payload = {"task": "new-worker-task", "inputs": {"text": 1}}
    response = TestClient(app).post(
        f"/tasks/{payload['task']}/runs", json={"inputs": payload["inputs"]}
    )
    assert response.status_code == 202
    assert client.enqueue.call_args.args[1] == payload


def test_registry_failure_is_sanitized(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    app.dependency_overrides.pop(get_database_connection)
    monkeypatch.setattr(
        "agora_api.api.deps.psycopg.connect",
        Mock(side_effect=psycopg.OperationalError("secret connection")),
    )
    response = TestClient(app).get("/tasks")
    assert response.status_code == 503
    assert "secret" not in response.text


def test_missing_registry_is_unavailable(
    app: FastAPI, registry: Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry.execute.return_value.fetchone.return_value = None
    app.dependency_overrides.pop(get_database_connection)
    connection_context = Mock()
    connection_context.__enter__ = Mock(return_value=registry)
    connection_context.__exit__ = Mock(return_value=False)
    monkeypatch.setattr("agora_api.api.deps.psycopg.connect", Mock(return_value=connection_context))
    response = TestClient(app).get("/tasks")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_new_task_result_is_retrievable() -> None:
    status = Mock(spec=WorkflowStatus)
    status.name = WORKFLOW_NAME
    status.application_name = APPLICATION_NAME
    status.status = "SUCCESS"
    status.input = {"args": [{"task": "new-worker-task", "inputs": {"text": "Hi"}}]}
    status.output = {"new-result-field": ["Hello", 42]}
    status.created_at = 1
    status.updated_at = 2
    client = Mock(spec=DBOSClient)
    client.retrieve_workflow.return_value.get_status.return_value = status
    workflow = get_run(client, str(uuid4()))
    assert workflow is not None
    assert workflow.result == status.output
