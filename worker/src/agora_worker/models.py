from pydantic import BaseModel, ConfigDict, Field, JsonValue


class TaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    task: str = Field(min_length=1)
    inputs: dict[str, JsonValue]


class OrchestrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    prompt: str = Field(min_length=1, max_length=20000)
    data: dict[str, JsonValue] = Field(default_factory=dict)
