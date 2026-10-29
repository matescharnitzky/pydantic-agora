from time import sleep

from dbos import DBOS, WorkflowSerializationFormat
from pydantic import JsonValue

from agora_worker.models import ScaleRequest, WaitRequest, WorkflowResult, request_adapter

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


@DBOS.step()
def wait(seconds: float) -> None:
    sleep(seconds)


@DBOS.workflow(name=WORKFLOW_NAME, serialization_type=WorkflowSerializationFormat.PORTABLE)
def execute(payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
    request = request_adapter.validate_python(payload)
    if isinstance(request, WaitRequest):
        wait(request.inputs.seconds)
        value = add(2, 3)
        return WorkflowResult(value=float(value), branch="unchanged").model_dump(mode="json")
    total = add(request.inputs.left, request.inputs.right)
    if isinstance(request, ScaleRequest):
        if request.inputs.double_positive and total > 0:
            result = WorkflowResult(value=float(double(total)), branch="doubled")
        else:
            result = WorkflowResult(value=float(total), branch="unchanged")
    else:
        result = WorkflowResult(value=divide(total, request.inputs.divisor), branch="divided")
    return result.model_dump(mode="json")
