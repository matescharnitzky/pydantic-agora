from time import sleep
from typing import Literal

from dbos import DBOS
from pydantic import Field

from agora_worker.models import ContractModel


class Numbers(ContractModel):
    left: int = Field(ge=-1_000_000, le=1_000_000)
    right: int = Field(ge=-1_000_000, le=1_000_000)


class ScaleInput(Numbers):
    double_positive: bool = False


class DivideInput(Numbers):
    divisor: int = Field(ge=-1_000_000, le=1_000_000)


class WaitInput(ContractModel):
    seconds: float = Field(ge=0.0, le=5.0)


class DummyOutput(ContractModel):
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


def add_then_scale(inputs: ScaleInput) -> DummyOutput:
    total = add(inputs.left, inputs.right)
    if inputs.double_positive and total > 0:
        return DummyOutput(value=float(double(total)), branch="doubled")
    return DummyOutput(value=float(total), branch="unchanged")


def divide_sum(inputs: DivideInput) -> DummyOutput:
    return DummyOutput(
        value=divide(add(inputs.left, inputs.right), inputs.divisor), branch="divided"
    )


def wait_then_add(inputs: WaitInput) -> DummyOutput:
    wait(inputs.seconds)
    return DummyOutput(value=float(add(2, 3)), branch="unchanged")
