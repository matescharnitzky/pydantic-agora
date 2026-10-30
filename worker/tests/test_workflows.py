import os
from collections.abc import Iterator
from time import monotonic, sleep

import pytest
from dbos import DBOSClient, DBOSPortableJSONSerializer, WorkflowHandle, WorkflowSerializationFormat

from agora_worker.config import Settings
from agora_worker.workflows import QUEUE_NAME, WORKFLOW_NAME

pytestmark = pytest.mark.integration


@pytest.fixture
def client() -> Iterator[DBOSClient]:
    if not os.environ.get("POSTGRES_PASSWORD"):
        pytest.fail("POSTGRES_PASSWORD is required for database integration tests", pytrace=False)
    client = DBOSClient(
        system_database_url=Settings().dbos_database_url,
        application_name="agora-worker",
        serializer=DBOSPortableJSONSerializer(),
        retry_connection_errors=False,
    )
    try:
        yield client
    finally:
        client.destroy()


def wait_for_status(handle: WorkflowHandle[object], expected_status: str) -> None:
    deadline = monotonic() + 20
    while monotonic() < deadline:
        status = handle.get_status().status
        if status == expected_status:
            return
        assert status in {"ENQUEUED", "PENDING"}, f"Unexpected workflow status: {status}"
        sleep(0.1)
    pytest.fail(f"Workflow did not reach {expected_status} within 20 seconds")


@pytest.mark.parametrize("fail", [False, True])
def test_worker_persists_successful_and_failed_steps(client: DBOSClient, fail: bool) -> None:
    handle: WorkflowHandle[object] = client.enqueue(
        {
            "queue_name": QUEUE_NAME,
            "workflow_name": WORKFLOW_NAME,
            "serialization_type": WorkflowSerializationFormat.PORTABLE,
        },
        {"task": "dummy", "inputs": {"left": 2, "right": 3, "fail": fail}},
    )
    wait_for_status(handle, "ERROR" if fail else "SUCCESS")
    steps = client.list_workflow_steps(handle.get_workflow_id())
    assert [step["function_name"] for step in steps] == ["wait", "add"]
    assert steps[0]["output"] is None
    if not fail:
        assert steps[1]["output"] == 5
        assert handle.get_result() == {"value": 5}


def test_worker_validates_inputs_independently(client: DBOSClient) -> None:
    handle: WorkflowHandle[object] = client.enqueue(
        {
            "queue_name": QUEUE_NAME,
            "workflow_name": WORKFLOW_NAME,
            "serialization_type": WorkflowSerializationFormat.PORTABLE,
        },
        {"task": "unregistered", "inputs": {}},
    )
    wait_for_status(handle, "ERROR")
    assert client.list_workflow_steps(handle.get_workflow_id()) == []
