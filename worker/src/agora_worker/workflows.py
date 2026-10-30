from time import sleep

from dbos import DBOS, WorkflowSerializationFormat
from pydantic import JsonValue

from agora_worker.generation import generate
from agora_worker.models import (
    DivideInputs,
    GenerationInputs,
    GenerationResult,
    ScaleInputs,
    WaitInputs,
    WorkflowRequest,
    WorkflowResult,
)
from agora_worker.registry import Capability

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


def add_then_scale(inputs: ScaleInputs) -> WorkflowResult:
    total = add(inputs.left, inputs.right)
    if inputs.double_positive and total > 0:
        return WorkflowResult(value=float(double(total)), branch="doubled")
    return WorkflowResult(value=float(total), branch="unchanged")


def divide_sum(inputs: DivideInputs) -> WorkflowResult:
    return WorkflowResult(
        value=divide(add(inputs.left, inputs.right), inputs.divisor), branch="divided"
    )


def wait_then_add(inputs: WaitInputs) -> WorkflowResult:
    wait(inputs.seconds)
    return WorkflowResult(value=float(add(2, 3)), branch="unchanged")


REGISTRY: list[Capability] = [
    Capability(
        id="generate",
        function=generate,
        input_model=GenerationInputs,
        output_model=GenerationResult,
        description="Generate text with an OpenAI model.",
        credentials=["OPENAI_API_KEY (worker)"],
    ),
    Capability(
        id="add_then_scale",
        function=add_then_scale,
        input_model=ScaleInputs,
        output_model=WorkflowResult,
        description="Add two numbers and optionally double a positive total.",
    ),
    Capability(
        id="divide_sum",
        function=divide_sum,
        input_model=DivideInputs,
        output_model=WorkflowResult,
        description="Add two numbers and divide their sum.",
    ),
    Capability(
        id="wait_then_add",
        function=wait_then_add,
        input_model=WaitInputs,
        output_model=WorkflowResult,
        description="Wait before adding two fixed numbers; used to verify recovery.",
    ),
]


@DBOS.workflow(name=WORKFLOW_NAME, serialization_type=WorkflowSerializationFormat.PORTABLE)
def execute(payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
    request = WorkflowRequest.model_validate(payload)
    capability = next((item for item in REGISTRY if item.id == request.operation), None)
    if capability is None:
        raise ValueError(f"Unknown operation: {request.operation}")
    return capability.call(request.inputs)
