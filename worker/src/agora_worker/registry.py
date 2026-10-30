from collections.abc import Callable
from dataclasses import dataclass

import psycopg
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field, JsonValue


class Capability(BaseModel):
    id: str
    description: str
    input_schema: dict[str, JsonValue]
    output_schema: dict[str, JsonValue]
    credentials: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class Handler:
    capability: Capability
    run: Callable[[dict[str, JsonValue]], dict[str, JsonValue]]


class Registry:
    def __init__(self, application: str = "agora-worker") -> None:
        self.application = application
        self.handlers: dict[str, Handler] = {}

    def register[Inputs: BaseModel, Result: BaseModel](
        self,
        operation: str,
        inputs: type[Inputs],
        result: type[Result],
        run: Callable[[Inputs], Result],
        *,
        description: str,
        input_schema: dict[str, JsonValue] | None = None,
        credentials: list[str] | None = None,
        constraints: list[str] | None = None,
    ) -> None:
        if operation in self.handlers:
            raise ValueError(f"Duplicate operation: {operation}")

        def invoke(payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
            return run(inputs.model_validate(payload)).model_dump(mode="json")

        self.handlers[operation] = Handler(
            Capability(
                id=operation,
                description=description,
                input_schema=input_schema
                if input_schema is not None
                else inputs.model_json_schema(),
                output_schema=result.model_json_schema(),
                credentials=credentials or [],
                constraints=constraints or [],
            ),
            invoke,
        )

    def execute(self, operation: str, inputs: dict[str, JsonValue]) -> dict[str, JsonValue]:
        handler = self.handlers.get(operation)
        if handler is None:
            raise ValueError(f"Unknown operation: {operation}")
        return handler.run(inputs)

    def capabilities(self) -> list[Capability]:
        return [handler.capability for handler in self.handlers.values()]

    def publish(self, database_url: str) -> None:
        # One atomic snapshot replaces metadata for this worker application, including removals.
        with psycopg.connect(database_url, connect_timeout=5) as connection:
            connection.execute("CREATE SCHEMA IF NOT EXISTS agora")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS agora.capability_registry ("
                "application text PRIMARY KEY, capabilities jsonb NOT NULL)"
            )
            connection.execute(
                "INSERT INTO agora.capability_registry (application, capabilities) VALUES (%s, %s) "
                "ON CONFLICT (application) DO UPDATE SET capabilities = EXCLUDED.capabilities",
                (
                    self.application,
                    Jsonb([item.model_dump(mode="json") for item in self.capabilities()]),
                ),
            )
