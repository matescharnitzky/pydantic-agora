from dbos import DBOS, WorkflowSerializationFormat
from pydantic import JsonValue, ValidationError

from agora_worker.models import TaskRequest
from agora_worker.orchestrator.agent import create_agent, run_orchestration
from agora_worker.tasks.execution import run_task

QUEUE_NAME = "agora-workflows-v1"
WORKFLOW_NAME = "agora.execute.v1"


@DBOS.workflow(name=WORKFLOW_NAME, serialization_type=WorkflowSerializationFormat.PORTABLE)
def execute(payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
    try:
        request = TaskRequest.model_validate(payload)
        return run_task(request.task, request.inputs)
    except ValidationError:
        # DBOS records exception text in traces; Pydantic errors can contain input values.
        raise ValueError("Invalid task data") from None


orchestration_agent = create_agent(lambda task, inputs: execute({"task": task, "inputs": inputs}))

ORCHESTRATION_WORKFLOW_NAME = "agora.orchestrate.v1"


@DBOS.workflow(
    name=ORCHESTRATION_WORKFLOW_NAME, serialization_type=WorkflowSerializationFormat.PORTABLE
)
def orchestrate(payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
    from agora_worker.models import OrchestrationRequest

    try:
        request = OrchestrationRequest.model_validate(payload)
        return run_orchestration(request, orchestration_agent)
    except Exception:
        raise ValueError("Orchestration failed") from None
