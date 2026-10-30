from collections.abc import Callable
from dataclasses import dataclass, field

import psycopg
from psycopg.types.json import Jsonb
from pydantic import BaseModel, JsonValue


@dataclass(frozen=True)
class Capability:
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


def register_capabilities(
    registry: list[Capability], database_url: str, *, application: str = "agora-worker"
) -> None:
    ids = [capability.id for capability in registry]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate capability id")
    with psycopg.connect(database_url, connect_timeout=5) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS agora")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS agora.capability_registry ("
            "application text PRIMARY KEY, capabilities jsonb NOT NULL)"
        )
        connection.execute(
            "INSERT INTO agora.capability_registry (application, capabilities) VALUES (%s, %s) "
            "ON CONFLICT (application) DO UPDATE SET capabilities = EXCLUDED.capabilities",
            (application, Jsonb([capability.metadata() for capability in registry])),
        )
