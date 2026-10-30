from collections.abc import Callable
from dataclasses import dataclass, field

import psycopg
from psycopg.types.json import Jsonb
from pydantic import BaseModel, JsonValue

from agora_worker.tasks.dummy.task import (
    DivideInputs,
    ScaleInputs,
    WaitInputs,
    WorkflowResult,
    add_then_scale,
    divide_sum,
    wait_then_add,
)
from agora_worker.tasks.generation.task import GenerationInputs, GenerationResult, generate


@dataclass(frozen=True)
class Task:
    id: str
    function: Callable[..., BaseModel]
    input_model: type[BaseModel]
    output_model: type[BaseModel]
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


TASK_REGISTRY: list[Task] = [
    Task(
        id="generate",
        function=generate,
        input_model=GenerationInputs,
        output_model=GenerationResult,
        description="Generate text with an OpenAI model.",
        credentials=["OPENAI_API_KEY (worker)"],
    ),
    Task(
        id="add_then_scale",
        function=add_then_scale,
        input_model=ScaleInputs,
        output_model=WorkflowResult,
        description="Add two numbers and optionally double a positive total.",
    ),
    Task(
        id="divide_sum",
        function=divide_sum,
        input_model=DivideInputs,
        output_model=WorkflowResult,
        description="Add two numbers and divide their sum.",
    ),
    Task(
        id="wait_then_add",
        function=wait_then_add,
        input_model=WaitInputs,
        output_model=WorkflowResult,
        description="Wait before adding two fixed numbers; used to verify recovery.",
    ),
]


def register_tasks(
    registry: list[Task], database_url: str, *, application: str = "agora-worker"
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
