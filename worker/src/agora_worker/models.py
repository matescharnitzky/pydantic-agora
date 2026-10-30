from typing import Literal

from jsonschema import Draft202012Validator, SchemaError
from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Numbers(ContractModel):
    left: int = Field(ge=-1_000_000, le=1_000_000)
    right: int = Field(ge=-1_000_000, le=1_000_000)


class ScaleInputs(Numbers):
    double_positive: bool = False


class DivideInputs(Numbers):
    divisor: int = Field(ge=-1_000_000, le=1_000_000)


class WaitInputs(ContractModel):
    seconds: float = Field(ge=0.0, le=5.0)


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


class WorkflowRequest(ContractModel):
    operation: str = Field(min_length=1)
    inputs: dict[str, JsonValue]


class WorkflowResult(ContractModel):
    value: float
    branch: Literal["unchanged", "doubled", "divided"]


class GenerationResult(ContractModel):
    output: JsonValue
    model: str
