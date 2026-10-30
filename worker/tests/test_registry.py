import os
from uuid import uuid4

import psycopg
import pytest
from pydantic import BaseModel, ValidationError

from agora_worker.config import Settings
from agora_worker.tasks.base import Task
from agora_worker.tasks.registry import register_tasks


class Inputs(BaseModel):
    text: str


class Result(BaseModel):
    length: int


class LengthTask(Task[Inputs, Result]):
    id = "length"
    description = "Count characters"
    input_model = Inputs
    output_model = Result

    def run(self, inputs: Inputs) -> Result:
        return Result(length=len(inputs.text))


def test_task_validates_inputs_and_calls_function() -> None:
    assert LengthTask().call({"text": "abc"}) == {"length": 3}
    with pytest.raises(ValidationError):
        LengthTask().call({"text": 1})


def test_duplicate_tasks_are_rejected_before_database_access() -> None:
    with pytest.raises(ValueError, match="Duplicate task"):
        register_tasks([LengthTask, LengthTask], "not-a-database-url")


@pytest.mark.integration
def test_registration_publishes_schemas_and_replaces_previous_catalog() -> None:
    if not os.environ.get("POSTGRES_PASSWORD"):
        pytest.fail("POSTGRES_PASSWORD is required for database integration tests", pytrace=False)
    database_url = str(Settings().database_url)
    application = f"registry-test-{uuid4()}"
    try:
        register_tasks([LengthTask], database_url, application=application)
        with psycopg.connect(database_url) as connection:
            row = connection.execute(
                "SELECT tasks FROM agora.task_registry WHERE application = %s",
                (application,),
            ).fetchone()
            assert row == ([LengthTask().metadata()],)
        register_tasks([], database_url, application=application)
        with psycopg.connect(database_url) as connection:
            row = connection.execute(
                "SELECT tasks FROM agora.task_registry WHERE application = %s",
                (application,),
            ).fetchone()
            assert row == ([],)
    finally:
        with psycopg.connect(database_url) as connection:
            connection.execute(
                "DELETE FROM agora.task_registry WHERE application = %s", (application,)
            )
