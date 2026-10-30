from collections.abc import Sequence
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from agora_worker.tasks.base import Task


def register_tasks(
    registry: Sequence[type[Task[Any, Any]]],
    database_url: str,
    *,
    application: str = "agora-worker",
) -> None:
    """Replace this application's task catalog in PostgreSQL during worker startup.

    Reject duplicate IDs before connecting. Create the schema/table if needed and commit
    the catalog atomically; constructing task instances must not require arguments.
    """
    ids = [task_type.id for task_type in registry]
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
            (application, Jsonb([task_type().metadata() for task_type in registry])),
        )
