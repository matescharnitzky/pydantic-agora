from pydantic import Field
from pydantic_ai import Agent
from pydantic_ai.durable_exec.dbos import DBOSDurability

from agora_worker.models import ContractModel


class GenerationInputs(ContractModel):
    prompt: str = Field(min_length=1)
    instructions: str = ""
    model: str = Field(default="gpt-5-mini", min_length=1)


class GenerationResult(ContractModel):
    output: str
    model: str


agent = Agent[GenerationInputs, str](
    "openai-responses:gpt-5-mini",
    name="agora_generate_v1",
    deps_type=GenerationInputs,
    output_type=str,
    defer_model_check=True,
    capabilities=[DBOSDurability()],
)


def generate(inputs: GenerationInputs) -> GenerationResult:
    result = agent.run_sync(
        inputs.prompt,
        instructions=inputs.instructions,
        model=f"openai-responses:{inputs.model}",
        deps=inputs,
    )
    return GenerationResult(output=result.output, model=result.response.model_name or inputs.model)
