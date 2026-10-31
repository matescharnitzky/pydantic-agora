from fastapi import APIRouter, Response

from agora_api.api.deps import WorkerClient
from agora_api.models import OrchestrationRequest, RunSubmission
from agora_api.services import runs

router = APIRouter(prefix="/orchestrations", tags=["orchestrations"])


@router.post("/runs", status_code=202, response_model=RunSubmission)
def submit_run(
    request: OrchestrationRequest, response: Response, client: WorkerClient
) -> RunSubmission:
    run_id = runs.submit_orchestration(client, request)
    response.headers["Location"] = f"/runs/{run_id}"
    return RunSubmission(id=run_id)
