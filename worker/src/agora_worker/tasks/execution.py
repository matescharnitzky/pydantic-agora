from pydantic import JsonValue, ValidationError

from agora_worker.tasks import TASK_REGISTRY


def run_task(task_id: str, inputs: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Single implementation path; callers provide the DBOS workflow boundary."""
    task_type = next((item for item in TASK_REGISTRY if item.id == task_id), None)
    if task_type is None:
        raise ValueError(f"Unknown task: {task_id}")
    try:
        task = task_type()
        validated = task.input_model.model_validate(inputs)
        result = task.run(validated)
        return task.output_model.model_validate(result).model_dump(mode="json")
    except ValidationError:
        raise ValueError("Invalid task data") from None
