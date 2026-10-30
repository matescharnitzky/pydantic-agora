from unittest.mock import Mock
from uuid import uuid4

import pytest
from dbos import DBOSClient, WorkflowStatus, error
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from agora_api.api.deps import get_workflow_client
from agora_api.services.workflows import APPLICATION_NAME, WORKFLOW_NAME, get_workflow


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("ENQUEUED", "waiting"),
        ("DELAYED", "waiting"),
        ("PENDING", "running"),
        ("SUCCESS", "successful"),
        ("ERROR", "failed"),
        ("CANCELLED", "failed"),
        ("MAX_RECOVERY_ATTEMPTS_EXCEEDED", "failed"),
    ],
)
def test_status_translation(status: str, expected: str) -> None:
    workflow = Mock(spec=WorkflowStatus)
    workflow.name = WORKFLOW_NAME
    workflow.application_name = APPLICATION_NAME
    workflow.input = {"args": [{"task": "add_then_scale", "inputs": {"left": 1, "right": 2}}]}
    workflow.status = status
    workflow.output = {"value": 3.0, "branch": "unchanged"}
    workflow.created_at = 1
    workflow.updated_at = 2
    client = Mock(spec=DBOSClient)
    client.retrieve_workflow.return_value.get_status.return_value = workflow
    workflow = get_workflow(client, str(uuid4()))
    assert workflow is not None
    assert workflow.status == expected
    assert workflow.model_dump(mode="json")["status"] == expected
    assert (workflow.result is not None) == (status == "SUCCESS")
    assert workflow.error == ("Workflow failed" if expected == "failed" else None)


def test_submission_only_enqueues_and_returns_location(app: FastAPI) -> None:
    client = Mock(spec=DBOSClient)
    app.dependency_overrides[get_workflow_client] = lambda: client
    response = TestClient(app).post(
        "/workflows",
        json={"task": "divide_sum", "inputs": {"left": 1, "right": 2, "divisor": 3}},
    )
    assert response.status_code == 202
    assert response.headers["Location"] == f"/workflows/{response.json()['id']}"
    client.enqueue.assert_called_once()
    client.retrieve_workflow.assert_not_called()


def test_unregistered_task_is_rejected_before_enqueuing(app: FastAPI) -> None:
    client = Mock(spec=DBOSClient)
    app.dependency_overrides[get_workflow_client] = lambda: client
    response = TestClient(app).post("/workflows", json={"task": "eval", "inputs": {}})
    assert response.status_code == 422
    client.enqueue.assert_not_called()


def test_database_failure_is_sanitized(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    client = Mock(spec=DBOSClient)
    client.enqueue.side_effect = OperationalError("secret connection", {}, Exception("secret"))
    monkeypatch.setattr("agora_api.api.deps.DBOSClient", Mock(return_value=client))
    response = TestClient(app).post(
        "/workflows", json={"task": "add_then_scale", "inputs": {"left": 1, "right": 2}}
    )
    assert response.status_code == 503
    assert "secret" not in response.text
    client.destroy.assert_called_once()


@pytest.mark.parametrize("field", ["name", "application_name"])
def test_other_workflows_are_not_exposed(field: str) -> None:
    workflow = Mock(spec=WorkflowStatus)
    workflow.name = WORKFLOW_NAME
    workflow.application_name = APPLICATION_NAME
    setattr(workflow, field, "another-workflow")
    client = Mock(spec=DBOSClient)
    client.retrieve_workflow.return_value.get_status.return_value = workflow
    assert get_workflow(client, str(uuid4())) is None


def test_missing_workflow_returns_none() -> None:
    workflow_id = str(uuid4())
    client = Mock(spec=DBOSClient)
    client.retrieve_workflow.side_effect = error.DBOSNonExistentWorkflowError(
        "target", str(workflow_id)
    )
    assert get_workflow(client, workflow_id) is None


def test_unknown_dbos_status_is_rejected() -> None:
    workflow = Mock(spec=WorkflowStatus)
    workflow.name = WORKFLOW_NAME
    workflow.application_name = APPLICATION_NAME
    workflow.input = {"args": [{"task": "add_then_scale", "inputs": {"left": 1, "right": 2}}]}
    workflow.status = "UNKNOWN"
    client = Mock(spec=DBOSClient)
    client.retrieve_workflow.return_value.get_status.return_value = workflow
    with pytest.raises(KeyError, match="UNKNOWN"):
        get_workflow(client, str(uuid4()))
