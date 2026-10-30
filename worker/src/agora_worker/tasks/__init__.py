from typing import Any

from agora_worker.tasks.base import Task
from agora_worker.tasks.dummy.task import AddThenScaleTask, DivideSumTask, WaitThenAddTask
from agora_worker.tasks.generation.task import GenerationTask

TASK_REGISTRY: list[type[Task[Any, Any]]] = [
    GenerationTask,
    AddThenScaleTask,
    DivideSumTask,
    WaitThenAddTask,
]
