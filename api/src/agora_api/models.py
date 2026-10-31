from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue


class RunInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    inputs: dict[str, JsonValue]


class TaskRequest(RunInput):
    task: str = Field(min_length=1)


class Task(BaseModel):
    id: str
    description: str
    input_schema: dict[str, JsonValue]
    output_schema: dict[str, JsonValue]


class Health(BaseModel):
    status: Literal["ok", "unavailable"]
    service: Literal["api"] = "api"


class RunStatus(StrEnum):
    WAITING = "waiting"
    RUNNING = "running"
    SUCCESSFUL = "successful"
    FAILED = "failed"


class RunSubmission(BaseModel):
    id: str
    status: RunStatus = RunStatus.WAITING


class Run(BaseModel):
    id: str
    status: RunStatus
    request: TaskRequest | OrchestrationRequest
    result: dict[str, JsonValue] | None = None
    error: str | None = None
    created_at: int | None = None
    updated_at: int | None = None


class OrchestrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    prompt: str = Field(min_length=1, max_length=20000)
    data: dict[str, JsonValue] = Field(default_factory=dict)
