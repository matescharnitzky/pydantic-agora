from pydantic import BaseModel, ConfigDict, Field, JsonValue


class TaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    task: str = Field(min_length=1)
    inputs: dict[str, JsonValue]
