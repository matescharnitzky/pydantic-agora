from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Numbers(ContractModel):
    left: int = Field(ge=-1_000_000, le=1_000_000)
    right: int = Field(ge=-1_000_000, le=1_000_000)


class ScaleInputs(Numbers):
    double_positive: bool = False


class DivideInputs(Numbers):
    divisor: int = Field(ge=-1_000_000, le=1_000_000)


class ScaleRequest(ContractModel):
    operation: Literal["add_then_scale"]
    inputs: ScaleInputs


class DivideRequest(ContractModel):
    operation: Literal["divide_sum"]
    inputs: DivideInputs


WorkflowRequest = Annotated[ScaleRequest | DivideRequest, Field(discriminator="operation")]
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
