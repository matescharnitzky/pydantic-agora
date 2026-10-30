from time import sleep
from typing import Literal

from dbos import DBOS
from pydantic import Field

from agora_worker.models import ContractModel


class Numbers(ContractModel):
    left: int = Field(ge=-1_000_000, le=1_000_000)
    right: int = Field(ge=-1_000_000, le=1_000_000)


class ScaleInputs(Numbers):
    double_positive: bool = False


class DivideInputs(Numbers):
    divisor: int = Field(ge=-1_000_000, le=1_000_000)


class WaitInputs(ContractModel):
    seconds: float = Field(ge=0.0, le=5.0)


class WorkflowResult(ContractModel):
    value: float
    branch: Literal["unchanged", "doubled", "divided"]


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
