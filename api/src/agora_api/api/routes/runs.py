from uuid import UUID

from fastapi import APIRouter, HTTPException

from agora_api.api.deps import WorkerClient
from agora_api.models import Run
from agora_api.services import runs

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/{run_id}", response_model=Run)
def get_run(run_id: UUID, client: WorkerClient) -> Run:
    """Return run status and output, or 404 for unknown or unrelated workflows."""
    run = runs.get_run(client, str(run_id))
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
