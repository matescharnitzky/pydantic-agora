from unittest.mock import Mock
from uuid import uuid4

import pytest
from dbos import DBOSClient, WorkflowStatus
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agora_api.api.deps import get_workflow_client
from agora_api.services.workflows import APPLICATION_NAME, WORKFLOW_NAME, get_workflow


def test_discovery_describes_generation_without_worker_credentials(app: FastAPI) -> None:
    response = TestClient(app).get("/capabilities")
    assert response.status_code == 200
    capability = response.json()[0]
    assert capability["id"] == "generate"
    assert "output_schema" in capability["input_schema"]["properties"]
    assert capability["credentials"] == ["OPENAI_API_KEY (worker)"]


def test_generation_request_is_enqueued_with_the_supplied_schema(app: FastAPI) -> None:
    client = Mock(spec=DBOSClient)
    app.dependency_overrides[get_workflow_client] = lambda: client
    inputs = {
        "prompt": "Extract Ada",
        "instructions": "Extract the name",
        "model": "gpt-5-mini",
        "output_schema": {"type": "object", "required": ["name"]},
    }
    response = TestClient(app).post("/workflows", json={"operation": "generate", "inputs": inputs})
    assert response.status_code == 202
    assert client.enqueue.call_args.args[1] == {"operation": "generate", "inputs": inputs}


@pytest.mark.parametrize(
    "inputs",
    [
        {"prompt": ""},
        {"prompt": "Generate", "output_schema": {"type": "imaginary"}},
        {"prompt": "Generate", "output_schema": {"$ref": "https://example.com/schema"}},
        {"prompt": "Generate", "output_schema": {"$schema": "draft-07"}},
    ],
)
def test_invalid_generation_is_rejected_before_enqueuing(
    app: FastAPI, inputs: dict[str, object]
) -> None:
    client = Mock(spec=DBOSClient)
    app.dependency_overrides[get_workflow_client] = lambda: client
    response = TestClient(app).post("/workflows", json={"operation": "generate", "inputs": inputs})
    assert response.status_code == 422
    client.enqueue.assert_not_called()


def test_generation_result_is_retrievable() -> None:
    status = Mock(spec=WorkflowStatus)
    status.name = WORKFLOW_NAME
    status.application_name = APPLICATION_NAME
    status.status = "SUCCESS"
    status.input = {"args": [{"operation": "generate", "inputs": {"prompt": "Say hello"}}]}
    status.output = {"output": "Hello", "model": "gpt-5-mini"}
    status.created_at = 1
    status.updated_at = 2
    client = Mock(spec=DBOSClient)
    client.retrieve_workflow.return_value.get_status.return_value = status
    workflow = get_workflow(client, str(uuid4()))
    assert workflow is not None
    assert workflow.result is not None
    assert workflow.result.model_dump() == status.output
