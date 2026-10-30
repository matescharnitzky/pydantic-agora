from fastapi import APIRouter

from agora_api.api.deps import DatabaseConnection
from agora_api.models import Task
from agora_api.services import tasks

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[Task])
def list_tasks(connection: DatabaseConnection) -> list[Task]:
    return tasks.list_tasks(connection)
