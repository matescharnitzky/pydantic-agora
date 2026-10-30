from time import sleep

from dbos import DBOS, WorkflowSerializationFormat
from pydantic import JsonValue

from agora_worker.generation import generate, generation_input_schema
from agora_worker.models import (
    DivideInputs,
    GenerationInputs,
    GenerationResult,
    ScaleInputs,
    WaitInputs,
    WorkflowRequest,
    WorkflowResult,
)
from agora_worker.registry import Registry

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


registry = Registry()
registry.register(
    "generate",
    GenerationInputs,
    GenerationResult,
    generate,
    description="Generate text or JSON matching a caller-supplied schema.",
    input_schema=generation_input_schema(),
    credentials=["OPENAI_API_KEY (worker)"],
    constraints=[
        "OpenAI Responses models only",
        "Inline JSON Schema draft 2020-12 schemas; references are not supported",
        "Provider-specific schema/model restrictions may cause execution to fail",
        "Local/private execution; no application cancellation or call-budget policy",
    ],
)
registry.register(
    "add_then_scale",
    ScaleInputs,
    WorkflowResult,
    add_then_scale,
    description="Add two numbers and optionally double a positive total.",
)
registry.register(
    "divide_sum",
    DivideInputs,
    WorkflowResult,
    divide_sum,
    description="Add two numbers and divide their sum.",
)
registry.register(
    "wait_then_add",
    WaitInputs,
    WorkflowResult,
    wait_then_add,
    description="Wait before adding two fixed numbers; used to verify recovery.",
)


@DBOS.workflow(name=WORKFLOW_NAME, serialization_type=WorkflowSerializationFormat.PORTABLE)
def execute(payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
    request = WorkflowRequest.model_validate(payload)
    return registry.execute(request.operation, request.inputs)
