from unittest.mock import Mock
from uuid import uuid4

import psycopg
import pytest
from dbos import DBOSClient, WorkflowStatus
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agora_api.api.deps import get_registry_connection, get_workflow_client
from agora_api.services.workflows import APPLICATION_NAME, WORKFLOW_NAME, get_workflow


@pytest.fixture
def registry(app: FastAPI) -> Mock:
    connection = Mock()
    connection.execute.return_value.fetchone.return_value = (
        [
            {
                "id": "new-worker-operation",
                "description": "Registered by the worker without API changes",
                "input_schema": {
                    "type": "object",
                    "properties": {"text": {"type": "string", "minLength": 1}},
                    "required": ["text"],
                    "additionalProperties": False,
                },
                "output_schema": {"type": "object"},
                "credentials": [],
                "constraints": [],
            }
        ],
    )
    app.dependency_overrides[get_registry_connection] = lambda: connection
    return connection


def test_discovery_reads_worker_metadata(app: FastAPI, registry: Mock) -> None:
    response = TestClient(app).get("/capabilities")
    assert response.status_code == 200
    assert response.json() == registry.execute.return_value.fetchone.return_value[0]


def test_new_worker_operation_is_enqueued_without_api_changes(app: FastAPI, registry: Mock) -> None:
    client = Mock(spec=DBOSClient)
    app.dependency_overrides[get_workflow_client] = lambda: client
    payload = {"operation": "new-worker-operation", "inputs": {"text": "Hello"}}
    response = TestClient(app).post("/workflows", json=payload)
    assert response.status_code == 202
    assert client.enqueue.call_args.args[1] == payload


@pytest.mark.parametrize("inputs", [{}, {"text": ""}, {"text": 1}, {"text": "hi", "extra": True}])
def test_published_schema_is_checked_before_enqueue(
    app: FastAPI, registry: Mock, inputs: dict[str, object]
) -> None:
    client = Mock(spec=DBOSClient)
    app.dependency_overrides[get_workflow_client] = lambda: client
    response = TestClient(app).post(
        "/workflows", json={"operation": "new-worker-operation", "inputs": inputs}
    )
    assert response.status_code == 422
    client.enqueue.assert_not_called()


def test_registry_failure_is_sanitized(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    app.dependency_overrides.pop(get_registry_connection)
    monkeypatch.setattr(
        "agora_api.api.deps.psycopg.connect",
        Mock(side_effect=psycopg.OperationalError("secret connection")),
    )
    response = TestClient(app).get("/capabilities")
    assert response.status_code == 503
    assert "secret" not in response.text


def test_missing_registry_is_unavailable(
    app: FastAPI, registry: Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry.execute.return_value.fetchone.return_value = None
    app.dependency_overrides.pop(get_registry_connection)
    connection_context = Mock()
    connection_context.__enter__ = Mock(return_value=registry)
    connection_context.__exit__ = Mock(return_value=False)
    monkeypatch.setattr("agora_api.api.deps.psycopg.connect", Mock(return_value=connection_context))
    response = TestClient(app).get("/capabilities")
    assert response.status_code == 503
    assert response.json() == {"detail": "Capability registry unavailable"}


def test_new_operation_result_is_retrievable() -> None:
    status = Mock(spec=WorkflowStatus)
    status.name = WORKFLOW_NAME
    status.application_name = APPLICATION_NAME
    status.status = "SUCCESS"
    status.input = {"args": [{"operation": "new-worker-operation", "inputs": {"text": "Hi"}}]}
    status.output = {"new-result-field": ["Hello", 42]}
    status.created_at = 1
    status.updated_at = 2
    client = Mock(spec=DBOSClient)
    client.retrieve_workflow.return_value.get_status.return_value = status
    workflow = get_workflow(client, str(uuid4()))
    assert workflow is not None
    assert workflow.result == status.output
