from time import sleep

from dbos import DBOS
from pydantic import BaseModel, ConfigDict, Field

from agora_worker.tasks.base import Task


class DummyInput(BaseModel):  # noqa: D101 - Simple data model.
    model_config = ConfigDict(extra="forbid", strict=True)

    left: int = Field(default=2, ge=-1_000_000, le=1_000_000)
    right: int = Field(default=3, ge=-1_000_000, le=1_000_000)
    seconds: float = Field(default=0.0, ge=0.0, le=5.0)
    fail: bool = False


class DummyOutput(BaseModel):  # noqa: D101 - Simple data model.
    model_config = ConfigDict(extra="forbid", strict=True)

    value: int


@DBOS.step()
def wait(seconds: float) -> None:
    """Block the worker for the requested delay as a durable DBOS step."""
    sleep(seconds)


@DBOS.step()
def add(left: int, right: int, fail: bool) -> int:
    """Raise an intentional failure when requested, otherwise persist the sum as a DBOS step."""
    if fail:
        raise ValueError("Dummy task failed")
    return left + right


class DummyTask(Task[DummyInput, DummyOutput]):
    """Exercise durable steps and workflow failure handling without external providers."""

    id = "dummy"
    description = "Wait and add numbers, with an optional failure for runtime checks."
    input_model = DummyInput
    output_model = DummyOutput

    def run(self, inputs: DummyInput) -> DummyOutput:
        """Wait before adding; an intentional failure happens after the delay completes."""
        wait(inputs.seconds)
        return DummyOutput(value=add(inputs.left, inputs.right, inputs.fail))
