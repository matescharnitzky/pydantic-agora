from uuid import uuid4

from dbos import DBOSClient, WorkflowSerializationFormat
from dbos import error as dbos_error

from agora_api.models import (
    Workflow,
    WorkflowRequest,
    WorkflowResult,
    WorkflowStatus,
    request_adapter,
)

QUEUE_NAME = "agora-workflows-v1"
WORKFLOW_NAME = "agora.execute.v1"
APPLICATION_NAME = "agora-worker"

STATUS_MAP = {
    "ENQUEUED": WorkflowStatus.WAITING,
    "DELAYED": WorkflowStatus.WAITING,
    "PENDING": WorkflowStatus.RUNNING,
    "SUCCESS": WorkflowStatus.SUCCESSFUL,
    "ERROR": WorkflowStatus.FAILED,
    "CANCELLED": WorkflowStatus.FAILED,
    "MAX_RECOVERY_ATTEMPTS_EXCEEDED": WorkflowStatus.FAILED,
}


def submit_workflow(client: DBOSClient, request: WorkflowRequest) -> str:
    workflow_id = str(uuid4())
    client.enqueue(
        {
            "workflow_id": workflow_id,
            "workflow_name": WORKFLOW_NAME,
            "queue_name": QUEUE_NAME,
            "serialization_type": WorkflowSerializationFormat.PORTABLE,
            "application_name": APPLICATION_NAME,
            "workflow_timeout": request.limits.timeout_seconds,
        },
        request.model_dump(mode="json"),
    )
    return workflow_id


def get_workflow(client: DBOSClient, workflow_id: str) -> Workflow | None:
    try:
        workflow = client.retrieve_workflow(workflow_id).get_status()
    except dbos_error.DBOSNonExistentWorkflowError:
        return None
    if workflow.name != WORKFLOW_NAME or workflow.application_name != APPLICATION_NAME:
        return None
    if workflow.input is None:
        raise ValueError("Missing persisted workflow input")
    request = request_adapter.validate_python(workflow.input["args"][0])
    status = workflow.status
    public_status = STATUS_MAP[status]
    if status == "CANCELLED":
        error = "Workflow cancelled or time limit exceeded"
    elif workflow.error is not None and str(workflow.error) == "Step budget exhausted":
        error = "Step budget exhausted"
    else:
        error = "Workflow failed" if public_status == WorkflowStatus.FAILED else None
    return Workflow(
        id=workflow_id,
        status=public_status,
        request=request,
        result=WorkflowResult.model_validate(workflow.output) if status == "SUCCESS" else None,
        error=error,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


def cancel_workflow(client: DBOSClient, workflow_id: str) -> Workflow | None:
    workflow = get_workflow(client, workflow_id)
    if workflow is None:
        return None
    if workflow.status in {WorkflowStatus.WAITING, WorkflowStatus.RUNNING}:
        client.cancel_workflow(workflow_id)
    return get_workflow(client, workflow_id)
