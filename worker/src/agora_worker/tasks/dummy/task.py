from time import sleep
from typing import Literal

from dbos import DBOS
from pydantic import BaseModel, ConfigDict, Field

from agora_worker.tasks.base import Task


class Numbers(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    left: int = Field(ge=-1_000_000, le=1_000_000)
    right: int = Field(ge=-1_000_000, le=1_000_000)


class ScaleInput(Numbers):
    double_positive: bool = False


class DivideInput(Numbers):
    divisor: int = Field(ge=-1_000_000, le=1_000_000)


class WaitInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    seconds: float = Field(ge=0.0, le=5.0)


class DummyOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

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


class AddThenScaleTask(Task[ScaleInput, DummyOutput]):
    id = "add_then_scale"
    description = "Add two numbers and optionally double a positive total."
    input_model = ScaleInput
    output_model = DummyOutput

    def run(self, inputs: ScaleInput) -> DummyOutput:
        total = add(inputs.left, inputs.right)
        if inputs.double_positive and total > 0:
            return DummyOutput(value=float(double(total)), branch="doubled")
        return DummyOutput(value=float(total), branch="unchanged")


class DivideSumTask(Task[DivideInput, DummyOutput]):
    id = "divide_sum"
    description = "Add two numbers and divide their sum."
    input_model = DivideInput
    output_model = DummyOutput

    def run(self, inputs: DivideInput) -> DummyOutput:
        return DummyOutput(
            value=divide(add(inputs.left, inputs.right), inputs.divisor), branch="divided"
        )


class WaitThenAddTask(Task[WaitInput, DummyOutput]):
    id = "wait_then_add"
    description = "Wait before adding two fixed numbers; used to verify recovery."
    input_model = WaitInput
    output_model = DummyOutput

    def run(self, inputs: WaitInput) -> DummyOutput:
        wait(inputs.seconds)
        return DummyOutput(value=float(add(2, 3)), branch="unchanged")
