from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue


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


class WorkflowRequest(ContractModel):
    operation: str = Field(min_length=1)
    inputs: dict[str, JsonValue]


class WorkflowResult(ContractModel):
    value: float
    branch: Literal["unchanged", "doubled", "divided"]


class GenerationResult(ContractModel):
    output: str
    model: str
