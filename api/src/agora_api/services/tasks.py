import psycopg
from pydantic import TypeAdapter

from agora_api.models import Task

task_adapter = TypeAdapter(list[Task])


def list_tasks(connection: psycopg.Connection[tuple[object, ...]]) -> list[Task]:
    """Validate the worker catalog stored in PostgreSQL; fail if it has not been registered."""
    row = connection.execute(
        "SELECT tasks FROM agora.task_registry WHERE application = %s",
        ("agora-worker",),
    ).fetchone()
    if row is None:
        raise psycopg.OperationalError("Task registry unavailable")
    return task_adapter.validate_python(row[0])


def validate_task(task_id: str, tasks: list[Task]) -> None:
    """Reject task IDs absent from the worker catalog before enqueueing a run."""
    if not any(task.id == task_id for task in tasks):
        raise ValueError("Unknown task")
