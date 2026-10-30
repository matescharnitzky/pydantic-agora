from collections.abc import Sequence
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from agora_worker.tasks.base import Task
from agora_worker.tasks.dummy.task import AddThenScaleTask, DivideSumTask, WaitThenAddTask
from agora_worker.tasks.generation.task import GenerationTask

TASK_REGISTRY: list[type[Task[Any, Any]]] = [
    GenerationTask,
    AddThenScaleTask,
    DivideSumTask,
    WaitThenAddTask,
]


def register_tasks(
    registry: Sequence[type[Task[Any, Any]]],
    database_url: str,
    *,
    application: str = "agora-worker",
) -> None:
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
