from pydantic import BaseModel, ConfigDict, Field, JsonValue


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class WorkflowRequest(ContractModel):
    task: str = Field(min_length=1)
    inputs: dict[str, JsonValue]
