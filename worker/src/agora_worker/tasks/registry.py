from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Protocol

import psycopg
from psycopg.types.json import Jsonb
from pydantic import BaseModel, JsonValue

from agora_worker.tasks.dummy.task import (
    DivideInput,
    DummyOutput,
    ScaleInput,
    WaitInput,
    add_then_scale,
    divide_sum,
    wait_then_add,
)
from agora_worker.tasks.generation.task import GenerationInput, GenerationOutput, generate


@dataclass(frozen=True)
class Task[InputT: BaseModel, OutputT: BaseModel]:
    id: str
    function: Callable[[InputT], OutputT]
    input_model: type[InputT]
    output_model: type[OutputT]
    description: str
    credentials: list[str] = field(default_factory=list[str])

    def metadata(self) -> dict[str, JsonValue]:
        return {
            "id": self.id,
            "description": self.description,
            "input_schema": self.input_model.model_json_schema(),
            "output_schema": self.output_model.model_json_schema(),
            "credentials": list[JsonValue](self.credentials),
        }

    def call(self, inputs: dict[str, JsonValue]) -> dict[str, JsonValue]:
        result = self.function(self.input_model.model_validate(inputs))
        return self.output_model.model_validate(result).model_dump(mode="json")


class RegisteredTask(Protocol):
    @property
    def id(self) -> str: ...

    def metadata(self) -> dict[str, JsonValue]: ...

    def call(self, inputs: dict[str, JsonValue]) -> dict[str, JsonValue]: ...


TASK_REGISTRY: list[RegisteredTask] = [
    Task[GenerationInput, GenerationOutput](
        id="generate",
        function=generate,
        input_model=GenerationInput,
        output_model=GenerationOutput,
        description="Generate text with an OpenAI model.",
        credentials=["OPENAI_API_KEY (worker)"],
    ),
    Task[ScaleInput, DummyOutput](
        id="add_then_scale",
        function=add_then_scale,
        input_model=ScaleInput,
        output_model=DummyOutput,
        description="Add two numbers and optionally double a positive total.",
    ),
    Task[DivideInput, DummyOutput](
        id="divide_sum",
        function=divide_sum,
        input_model=DivideInput,
        output_model=DummyOutput,
        description="Add two numbers and divide their sum.",
    ),
    Task[WaitInput, DummyOutput](
        id="wait_then_add",
        function=wait_then_add,
        input_model=WaitInput,
        output_model=DummyOutput,
        description="Wait before adding two fixed numbers; used to verify recovery.",
    ),
]


def register_tasks(
    registry: Sequence[RegisteredTask], database_url: str, *, application: str = "agora-worker"
) -> None:
    ids = [task.id for task in registry]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate task id")
    with psycopg.connect(database_url, connect_timeout=5) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS agora")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS agora.task_registry ("
            "application text PRIMARY KEY, tasks jsonb NOT NULL)"
        )
        connection.execute(
            "INSERT INTO agora.task_registry (application, tasks) VALUES (%s, %s) "
            "ON CONFLICT (application) DO UPDATE SET tasks = EXCLUDED.tasks",
            (application, Jsonb([task.metadata() for task in registry])),
        )
