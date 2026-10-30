from enum import StrEnum
from typing import Annotated, Literal

from jsonschema import Draft202012Validator, SchemaError
from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter, model_validator


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


class WaitInputs(ContractModel):
    seconds: float = Field(ge=0.0, le=5.0)


class WaitRequest(ContractModel):
    operation: Literal["wait_then_add"]
    inputs: WaitInputs


class GenerationInputs(ContractModel):
    prompt: str = Field(min_length=1)
    instructions: str = ""
    model: str = Field(default="gpt-5-mini", min_length=1)
    output_schema: dict[str, JsonValue] | None = None

    @model_validator(mode="after")
    def validate_output_schema(self) -> "GenerationInputs":
        schema = self.output_schema
        if schema is None:
            return self
        if schema.get("$schema", "https://json-schema.org/draft/2020-12/schema") != (
            "https://json-schema.org/draft/2020-12/schema"
        ):
            raise ValueError("Only JSON Schema draft 2020-12 is supported")
        pending: list[JsonValue] = [schema]
        while pending:
            node = pending.pop()
            if isinstance(node, dict):
                if "$ref" in node or "$dynamicRef" in node:
                    raise ValueError("output_schema must be inline; references are not supported")
                pending.extend(node.values())
            elif isinstance(node, list):
                pending.extend(node)
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError:
            raise ValueError("Invalid JSON Schema") from None
        return self


class GenerationRequest(ContractModel):
    operation: Literal["generate"]
    inputs: GenerationInputs


WorkflowRequest = Annotated[
    ScaleRequest | DivideRequest | WaitRequest | GenerationRequest, Field(discriminator="operation")
]
request_adapter = TypeAdapter(WorkflowRequest)


class WorkflowResult(ContractModel):
    value: float
    branch: Literal["unchanged", "doubled", "divided"]


class GenerationResult(ContractModel):
    output: JsonValue
    model: str


class Capability(BaseModel):
    id: str
    description: str
    input_schema: dict[str, JsonValue]
    output_schema: dict[str, JsonValue]
    credentials: list[str]
    constraints: list[str]


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
    result: WorkflowResult | GenerationResult | None = None
    error: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
