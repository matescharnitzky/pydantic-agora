from fastapi import APIRouter, HTTPException, Response

from agora_api.api.deps import DatabaseConnection, WorkerClient
from agora_api.models import RunInput, RunSubmission, Task
from agora_api.services import runs, tasks

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[Task])
def list_tasks(connection: DatabaseConnection) -> list[Task]:
    """Read the task catalog published by the worker at startup."""
    return tasks.list_tasks(connection)


@router.post("/{task_id}/runs", status_code=202, response_model=RunSubmission)
def submit_run(
    task_id: str,
    request: RunInput,
    response: Response,
    client: WorkerClient,
    connection: DatabaseConnection,
) -> RunSubmission:
    """Run a registered task; its inputs are validated by the worker."""
    try:
        tasks.validate_task(task_id, tasks.list_tasks(connection))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    run_id = runs.submit_run(client, task_id, request)
    response.headers["Location"] = f"/runs/{run_id}"
    return RunSubmission(id=run_id)
