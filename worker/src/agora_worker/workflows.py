from dbos import DBOS, WorkflowSerializationFormat
from pydantic import JsonValue

from agora_worker.models import TaskRequest
from agora_worker.tasks import TASK_REGISTRY

QUEUE_NAME = "agora-workflows-v1"
WORKFLOW_NAME = "agora.execute.v1"


@DBOS.workflow(name=WORKFLOW_NAME, serialization_type=WorkflowSerializationFormat.PORTABLE)
def execute(payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
    request = TaskRequest.model_validate(payload)
    task_type = next((item for item in TASK_REGISTRY if item.id == request.task), None)
    if task_type is None:
        raise ValueError(f"Unknown task: {request.task}")
    return task_type().call(request.inputs)
