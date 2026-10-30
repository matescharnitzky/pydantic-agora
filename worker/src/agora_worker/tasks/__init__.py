from typing import Any

from agora_worker.tasks.base import Task
from agora_worker.tasks.dummy.task import DummyTask
from agora_worker.tasks.generation.task import GenerationTask
from agora_worker.tasks.parsing.task import ParsingTask

TASK_REGISTRY: list[type[Task[Any, Any]]] = [
    GenerationTask,
    DummyTask,
    ParsingTask,
]
