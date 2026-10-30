from dbos import DBOS, WorkflowSerializationFormat
from pydantic import JsonValue, ValidationError

from agora_worker.models import TaskRequest
from agora_worker.tasks import TASK_REGISTRY

QUEUE_NAME = "agora-workflows-v1"
WORKFLOW_NAME = "agora.execute.v1"


@DBOS.workflow(name=WORKFLOW_NAME, serialization_type=WorkflowSerializationFormat.PORTABLE)
def execute(payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Validate a queued request, run its registered task, and serialize the output.

    Replace Pydantic error details to keep input values out of recorded exceptions;
    other task failures propagate to DBOS.
    """
    try:
        request = TaskRequest.model_validate(payload)
        task_type = next((item for item in TASK_REGISTRY if item.id == request.task), None)
        if task_type is None:
            raise ValueError(f"Unknown task: {request.task}")
        task = task_type()
        inputs = task.input_model.model_validate(request.inputs)
        output = task.run(inputs)
        return output.model_dump(mode="json")
    except ValidationError:
        # DBOS records exception text in traces; Pydantic errors can contain input values.
        raise ValueError("Invalid task data") from None
