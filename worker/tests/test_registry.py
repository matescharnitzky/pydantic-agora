import os
from uuid import uuid4

import psycopg
import pytest
from pydantic import BaseModel, ValidationError

from agora_worker.config import Settings
from agora_worker.registry import Capability, register_capabilities


class Inputs(BaseModel):
    text: str


class Result(BaseModel):
    length: int


def length(inputs: Inputs) -> Result:
    return Result(length=len(inputs.text))


capability = Capability(
    id="length",
    function=length,
    input_model=Inputs,
    output_model=Result,
    description="Count characters",
)


def test_capability_validates_inputs_and_calls_function() -> None:
    assert capability.call({"text": "abc"}) == {"length": 3}
    with pytest.raises(ValidationError):
        capability.call({"text": 1})


def test_duplicate_capabilities_are_rejected_before_database_access() -> None:
    with pytest.raises(ValueError, match="Duplicate capability"):
        register_capabilities([capability, capability], "not-a-database-url")


@pytest.mark.integration
def test_registration_publishes_schemas_and_replaces_previous_catalog() -> None:
    if not os.environ.get("POSTGRES_PASSWORD"):
        pytest.fail("POSTGRES_PASSWORD is required for database integration tests", pytrace=False)
    database_url = str(Settings().database_url)
    application = f"registry-test-{uuid4()}"
    try:
        register_capabilities([capability], database_url, application=application)
        with psycopg.connect(database_url) as connection:
            row = connection.execute(
                "SELECT capabilities FROM agora.capability_registry WHERE application = %s",
                (application,),
            ).fetchone()
            assert row == ([capability.metadata()],)
        register_capabilities([], database_url, application=application)
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
