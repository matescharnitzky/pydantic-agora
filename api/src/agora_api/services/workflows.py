from uuid import uuid4

from dbos import DBOSClient, WorkflowSerializationFormat, error
from opentelemetry.context import get_current
from sqlalchemy.exc import SQLAlchemyError

from agora_api.models import (
    Workflow,
    WorkflowRequest,
    WorkflowStatus,
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
    try:
        client.enqueue(
            {
                "workflow_id": workflow_id,
                "workflow_name": WORKFLOW_NAME,
                "queue_name": QUEUE_NAME,
                "serialization_type": WorkflowSerializationFormat.PORTABLE,
                "application_name": APPLICATION_NAME,
                "otel_context": get_current(),
            },
            request.model_dump(mode="json"),
        )
    except SQLAlchemyError:
        raise SQLAlchemyError("Workflow storage unavailable") from None
    return workflow_id


def get_workflow(client: DBOSClient, workflow_id: str) -> Workflow | None:
    try:
        workflow = client.retrieve_workflow(workflow_id).get_status()
    except error.DBOSNonExistentWorkflowError:
        return None
    except SQLAlchemyError:
        raise SQLAlchemyError("Workflow storage unavailable") from None
    if workflow.name != WORKFLOW_NAME or workflow.application_name != APPLICATION_NAME:
        return None
    if workflow.input is None:
        raise ValueError("Missing persisted workflow input")
    request = WorkflowRequest.model_validate(workflow.input["args"][0])
    status = workflow.status
    public_status = STATUS_MAP[status]
    return Workflow(
        id=workflow_id,
        status=public_status,
        request=request,
        result=workflow.output if status == "SUCCESS" else None,
        error="Workflow failed" if public_status == WorkflowStatus.FAILED else None,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )
