import os
from typing import cast
from uuid import uuid4

import psycopg
import pytest
from jsonschema import Draft202012Validator
from jsonschema.protocols import Validator
from pydantic import BaseModel, JsonValue, ValidationError

from agora_worker.config import Settings
from agora_worker.generation import generation_input_schema
from agora_worker.registry import Registry


class Inputs(BaseModel):
    text: str


class Result(BaseModel):
    length: int


def length(inputs: Inputs) -> Result:
    return Result(length=len(inputs.text))


def test_register_and_dispatch_new_operation() -> None:
    registry = Registry()
    registry.register("length", Inputs, Result, length, description="Count characters")
    assert registry.execute("length", {"text": "abc"}) == {"length": 3}
    with pytest.raises(ValidationError):
        registry.execute("length", {"text": 1})
    with pytest.raises(ValueError, match="Unknown operation"):
        registry.execute("unknown", {})
    with pytest.raises(ValueError, match="Duplicate operation"):
        registry.register("length", Inputs, Result, length, description="Count characters")


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "imaginary"},
        {"$ref": "https://example.com/schema"},
        {"properties": {"value": {"$ref": "#/$defs/value"}}},
        {"$schema": "draft-07"},
    ],
)
def test_published_generation_schema_rejects_unsupported_schemas(
    schema: dict[str, JsonValue],
) -> None:
    validator = cast(Validator, Draft202012Validator(generation_input_schema()))
    assert not validator.is_valid({"prompt": "Generate", "output_schema": schema})


@pytest.mark.parametrize(
    "schema",
    [
        None,
        {"type": "string"},
        {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
    ],
)
def test_published_generation_schema_accepts_supported_schemas(schema: JsonValue) -> None:
    validator = cast(Validator, Draft202012Validator(generation_input_schema()))
    assert validator.is_valid({"prompt": "Generate", "output_schema": schema})


@pytest.mark.integration
def test_registry_publication_replaces_previous_snapshot() -> None:
    if not os.environ.get("POSTGRES_PASSWORD"):
        pytest.fail("POSTGRES_PASSWORD is required for database integration tests", pytrace=False)
    database_url = str(Settings().database_url)
    application = f"registry-test-{uuid4()}"
    registry = Registry(application)
    registry.register("length", Inputs, Result, length, description="Count characters")
    try:
        registry.publish(database_url)
        with psycopg.connect(database_url) as connection:
            row = connection.execute(
                "SELECT capabilities FROM agora.capability_registry WHERE application = %s",
                (application,),
            ).fetchone()
            assert row is not None
            assert row[0] == [item.model_dump(mode="json") for item in registry.capabilities()]
        Registry(application).publish(database_url)
        with psycopg.connect(database_url) as connection:
            row = connection.execute(
                "SELECT capabilities FROM agora.capability_registry WHERE application = %s",
                (application,),
            ).fetchone()
            assert row == ([],)
    finally:
        with psycopg.connect(database_url) as connection:
            connection.execute(
                "DELETE FROM agora.capability_registry WHERE application = %s", (application,)
            )
