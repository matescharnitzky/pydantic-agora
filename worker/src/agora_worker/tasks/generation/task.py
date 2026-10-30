from typing import ClassVar

from pydantic import Field
from pydantic_ai import Agent
from pydantic_ai.durable_exec.dbos import DBOSDurability

from agora_worker.models import ContractModel
from agora_worker.tasks.base import Task


class GenerationInput(ContractModel):
    prompt: str = Field(min_length=1)
    instructions: str = ""
    model: str = Field(default="gpt-5-mini", min_length=1)


class GenerationOutput(ContractModel):
    output: str
    model: str


class GenerationTask(Task[GenerationInput, GenerationOutput]):
    id = "generate"
    description = "Generate text with an OpenAI model."
    input_model = GenerationInput
    output_model = GenerationOutput

    agent: ClassVar[Agent[GenerationInput, str]] = Agent(
        "openai-responses:gpt-5-mini",
        name="agora_generate_v1",
        deps_type=GenerationInput,
        output_type=str,
        defer_model_check=True,
        capabilities=[DBOSDurability()],
    )

    def run(self, inputs: GenerationInput) -> GenerationOutput:
        result = self.agent.run_sync(
            inputs.prompt,
            instructions=inputs.instructions,
            model=f"openai-responses:{inputs.model}",
            deps=inputs,
        )
        return GenerationOutput(
            output=result.output, model=result.response.model_name or inputs.model
        )
