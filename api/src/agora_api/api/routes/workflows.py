from uuid import UUID

from fastapi import APIRouter, HTTPException, Response

from agora_api.api.deps import RegistryConnection, WorkflowClient
from agora_api.models import Workflow, WorkflowRequest, WorkflowSubmission
from agora_api.services import capabilities, workflows

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("", status_code=202, response_model=WorkflowSubmission)
def submit_workflow(
    request: WorkflowRequest,
    response: Response,
    client: WorkflowClient,
    connection: RegistryConnection,
) -> WorkflowSubmission:
    try:
        capabilities.validate_request(request, capabilities.list_capabilities(connection))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    workflow_id = workflows.submit_workflow(client, request)
    response.headers["Location"] = f"/workflows/{workflow_id}"
    return WorkflowSubmission(id=workflow_id)


@router.get("/{workflow_id}", response_model=Workflow)
def get_workflow(workflow_id: UUID, client: WorkflowClient) -> Workflow:
    workflow = workflows.get_workflow(client, str(workflow_id))
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow
