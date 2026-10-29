from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class WorkflowLimits(ContractModel):
    timeout_seconds: float = Field(default=10.0, ge=0.1, le=30.0)
    max_calls: int = Field(default=4, ge=1, le=4)


class OperationRequest(ContractModel):
    limits: WorkflowLimits = Field(default_factory=WorkflowLimits)


class Numbers(ContractModel):
    left: int = Field(ge=-1_000_000, le=1_000_000)
    right: int = Field(ge=-1_000_000, le=1_000_000)


class ScaleInputs(Numbers):
    double_positive: bool = False


class DivideInputs(Numbers):
    divisor: int = Field(ge=-1_000_000, le=1_000_000)


class ScaleRequest(OperationRequest):
    operation: Literal["add_then_scale"]
    inputs: ScaleInputs


class DivideRequest(OperationRequest):
    operation: Literal["divide_sum"]
    inputs: DivideInputs


class WaitInputs(ContractModel):
    seconds: float = Field(ge=0.0, le=5.0)
    retry_once: bool = False


class WaitRequest(OperationRequest):
    operation: Literal["wait_then_add"]
    inputs: WaitInputs


WorkflowRequest = Annotated[
    ScaleRequest | DivideRequest | WaitRequest, Field(discriminator="operation")
]
request_adapter = TypeAdapter(WorkflowRequest)


class WorkflowResult(ContractModel):
    value: float
    branch: Literal["unchanged", "doubled", "divided"]


class Health(BaseModel):
    status: Literal["ok", "unavailable"]
    service: Literal["api"] = "api"


class WorkflowStatus(StrEnum):
    WAITING = "waiting"
    RUNNING = "running"
    SUCCESSFUL = "successful"
    FAILED = "failed"


class WorkflowSubmission(BaseModel):
    id: str
    status: WorkflowStatus = WorkflowStatus.WAITING


class Workflow(BaseModel):
    id: str
    status: WorkflowStatus
    request: WorkflowRequest
    result: WorkflowResult | None = None
    error: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
