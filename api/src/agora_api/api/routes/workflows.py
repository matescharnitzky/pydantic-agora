from uuid import UUID

from fastapi import APIRouter, HTTPException, Response

from agora_api.api.deps import WorkflowClient
from agora_api.models import Workflow, WorkflowRequest, WorkflowSubmission
from agora_api.services import workflows

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("", status_code=202, response_model=WorkflowSubmission)
def submit_workflow(
    request: WorkflowRequest, response: Response, client: WorkflowClient
) -> WorkflowSubmission:
    workflow_id = workflows.submit_workflow(client, request)
    response.headers["Location"] = f"/workflows/{workflow_id}"
    return WorkflowSubmission(id=workflow_id)


@router.get("/{workflow_id}", response_model=Workflow)
def get_workflow(workflow_id: UUID, client: WorkflowClient) -> Workflow:
    workflow = workflows.get_workflow(client, str(workflow_id))
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.post("/{workflow_id}/cancel", response_model=Workflow)
def cancel_workflow(workflow_id: UUID, client: WorkflowClient) -> Workflow:
    workflow = workflows.cancel_workflow(client, str(workflow_id))
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow
