from dbos import DBOS, WorkflowSerializationFormat
from pydantic import JsonValue

from agora_worker.models import ScaleRequest, WorkflowResult, request_adapter

QUEUE_NAME = "agora-workflows-v1"
WORKFLOW_NAME = "agora.execute.v1"


@DBOS.step()
def add(left: int, right: int) -> int:
    return left + right


@DBOS.step()
def double(value: int) -> int:
    return value * 2


@DBOS.step()
def divide(value: int, divisor: int) -> float:
    return value / divisor


@DBOS.workflow(name=WORKFLOW_NAME, serialization_type=WorkflowSerializationFormat.PORTABLE)
def execute(payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
    request = request_adapter.validate_python(payload)
    total = add(request.inputs.left, request.inputs.right)
    if isinstance(request, ScaleRequest):
        if request.inputs.double_positive and total > 0:
            result = WorkflowResult(value=float(double(total)), branch="doubled")
        else:
            result = WorkflowResult(value=float(total), branch="unchanged")
    else:
        result = WorkflowResult(value=divide(total, request.inputs.divisor), branch="divided")
    return result.model_dump(mode="json")
