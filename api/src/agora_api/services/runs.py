from uuid import uuid4

from dbos import DBOSClient, WorkflowSerializationFormat, error
from opentelemetry.context import get_current
from sqlalchemy.exc import SQLAlchemyError

from agora_api.models import (
    Run,
    RunInput,
    RunStatus,
    TaskRequest,
)

QUEUE_NAME = "agora-workflows-v1"
WORKFLOW_NAME = "agora.execute.v1"
APPLICATION_NAME = "agora-worker"

STATUS_MAP = {
    "ENQUEUED": RunStatus.WAITING,
    "DELAYED": RunStatus.WAITING,
    "PENDING": RunStatus.RUNNING,
    "SUCCESS": RunStatus.SUCCESSFUL,
    "ERROR": RunStatus.FAILED,
    "CANCELLED": RunStatus.FAILED,
    "MAX_RECOVERY_ATTEMPTS_EXCEEDED": RunStatus.FAILED,
}


def submit_run(client: DBOSClient, task_id: str, request: RunInput) -> str:
    run_id = str(uuid4())
    try:
        client.enqueue(
            {
                "workflow_id": run_id,
                "workflow_name": WORKFLOW_NAME,
                "queue_name": QUEUE_NAME,
                "serialization_type": WorkflowSerializationFormat.PORTABLE,
                "application_name": APPLICATION_NAME,
                "otel_context": get_current(),
            },
            TaskRequest(task=task_id, inputs=request.inputs).model_dump(mode="json"),
        )
    except SQLAlchemyError:
        raise SQLAlchemyError("Run storage unavailable") from None
    return run_id


def get_run(client: DBOSClient, run_id: str) -> Run | None:
    try:
        workflow = client.retrieve_workflow(run_id).get_status()
    except error.DBOSNonExistentWorkflowError:
        return None
    except SQLAlchemyError:
        raise SQLAlchemyError("Run storage unavailable") from None
    if workflow.name != WORKFLOW_NAME or workflow.application_name != APPLICATION_NAME:
        return None
    if workflow.input is None:
        raise ValueError("Missing persisted task input")
    request = TaskRequest.model_validate(workflow.input["args"][0])
    status = workflow.status
    public_status = STATUS_MAP[status]
    return Run(
        id=run_id,
        status=public_status,
        request=request,
        result=workflow.output if status == "SUCCESS" else None,
        error="Run failed" if public_status == RunStatus.FAILED else None,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )
