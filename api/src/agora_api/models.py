from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue


class WorkflowRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    task: str = Field(min_length=1)
    inputs: dict[str, JsonValue]


class Task(BaseModel):
    id: str
    description: str
    input_schema: dict[str, JsonValue]
    output_schema: dict[str, JsonValue]
    credentials: list[str]


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
    result: dict[str, JsonValue] | None = None
    error: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
