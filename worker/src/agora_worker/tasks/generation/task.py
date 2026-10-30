from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Agent
from pydantic_ai.durable_exec.dbos import DBOSDurability

from agora_worker.tasks.base import Task


class GenerationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    prompt: str = Field(min_length=1)
    instructions: str = ""


class GenerationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    output: str


class GenerationTask(Task[GenerationInput, GenerationOutput]):
    id = "generate"
    description = "Generate text with an OpenAI model."
    input_model = GenerationInput
    output_model = GenerationOutput

    agent: ClassVar[Agent[GenerationInput, str]] = Agent(
        "openai-responses:gpt-5-mini",
        name="generate",
        deps_type=GenerationInput,
        output_type=str,
        defer_model_check=True,
        capabilities=[DBOSDurability()],
    )

    def run(self, inputs: GenerationInput) -> GenerationOutput:
        """Apply request instructions without changing the shared agent configuration."""
        result = self.agent.run_sync(
            inputs.prompt,
            instructions=inputs.instructions,
            deps=inputs,
        )
        return GenerationOutput(output=result.output)
