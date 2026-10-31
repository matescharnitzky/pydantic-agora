from unittest.mock import Mock
from uuid import uuid4

import pytest
from dbos import DBOSClient, WorkflowStatus
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agora_api.api.deps import get_worker_client
from agora_api.models import OrchestrationRequest
from agora_api.services.runs import APPLICATION_NAME, ORCHESTRATION_WORKFLOW_NAME, get_run


def test_submit_orchestration(app: FastAPI) -> None:
    client = Mock(spec=DBOSClient)
    app.dependency_overrides[get_worker_client] = lambda: client
    payload = {"prompt": "Review", "data": {"documents": ["first"]}}
    response = TestClient(app).post("/orchestrations/runs", json=payload)
    assert response.status_code == 202
    assert response.headers["location"] == f"/runs/{response.json()['id']}"
    assert client.enqueue.call_args.args[0]["workflow_name"] == ORCHESTRATION_WORKFLOW_NAME
    assert client.enqueue.call_args.args[1] == payload


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"prompt": ""},
        {"prompt": 42},
        {"prompt": "go", "data": []},
        {"prompt": "go", "task": "dummy"},
    ],
)
def test_invalid_request(app: FastAPI, payload: dict[str, object]) -> None:
    client = Mock(spec=DBOSClient)
    app.dependency_overrides[get_worker_client] = lambda: client
    assert TestClient(app).post("/orchestrations/runs", json=payload).status_code == 422
    client.enqueue.assert_not_called()


@pytest.mark.parametrize("state", ["SUCCESS", "ERROR"])
def test_retrieve_orchestration(state: str) -> None:
    status = Mock(spec=WorkflowStatus)
    status.name = ORCHESTRATION_WORKFLOW_NAME
    status.application_name = APPLICATION_NAME
    status.status = state
    status.input = {"args": [{"prompt": "Review", "data": {}}]}
    status.output = {"output": "done"}
    status.created_at = 1
    status.updated_at = 2
    client = Mock(spec=DBOSClient)
    client.retrieve_workflow.return_value.get_status.return_value = status
    run = get_run(client, str(uuid4()))
    assert run is not None and isinstance(run.request, OrchestrationRequest)
    assert run.result == (status.output if state == "SUCCESS" else None)
    assert run.error == ("Run failed" if state == "ERROR" else None)
