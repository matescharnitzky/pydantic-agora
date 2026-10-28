from collections.abc import Callable
from time import sleep
from typing import ParamSpec, TypeVar

import logfire
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


class TransientDummyError(RuntimeError):
    pass


def retry_dummy(error: BaseException) -> bool:
    return isinstance(error, TransientDummyError)


@DBOS.step(retries_allowed=True, max_attempts=2, interval_seconds=0.05, should_retry=retry_dummy)
def wait(seconds: float, retry_once: bool) -> None:
    step_status = DBOS.step_status
    attempt = (step_status.current_attempt or 0) if step_status is not None else 0
    with logfire.span("Wait attempt", workflow_id=DBOS.workflow_id, attempt=attempt):
        if retry_once and attempt == 0:
            logfire.warn("Retrying dummy step", workflow_id=DBOS.workflow_id, attempt=attempt)
            raise TransientDummyError("Transient dummy failure")
        sleep(seconds)


P = ParamSpec("P")
R = TypeVar("R")


class CallBudget:
    def __init__(self, maximum: int) -> None:
        self.maximum = maximum
        self.calls = 0

    def call(self, cost: int, function: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        if self.calls + cost > self.maximum:
            logfire.warn("Step budget exhausted", workflow_id=DBOS.workflow_id)
            raise ValueError("Step budget exhausted")
        self.calls += cost
        with logfire.span(
            "Approved call",
            workflow_id=DBOS.workflow_id,
            step=function.__name__,
            call_number=self.calls,
            reserved_attempts=cost,
        ):
            return function(*args, **kwargs)


@DBOS.workflow(name=WORKFLOW_NAME, serialization_type=WorkflowSerializationFormat.PORTABLE)
def execute(payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
    request = request_adapter.validate_python(payload)
    budget = CallBudget(request.limits.max_calls)
    if isinstance(request, WaitRequest):
        budget.call(2, wait, request.inputs.seconds, request.inputs.retry_once)
        value = budget.call(1, add, 2, 3)
        return WorkflowResult(value=float(value), branch="unchanged").model_dump(mode="json")
    total = budget.call(1, add, request.inputs.left, request.inputs.right)
    if isinstance(request, ScaleRequest):
        if request.inputs.double_positive and total > 0:
            result = WorkflowResult(value=float(budget.call(1, double, total)), branch="doubled")
        else:
            result = WorkflowResult(value=float(total), branch="unchanged")
    else:
        result = WorkflowResult(
            value=budget.call(1, divide, total, request.inputs.divisor), branch="divided"
        )
    return result.model_dump(mode="json")
