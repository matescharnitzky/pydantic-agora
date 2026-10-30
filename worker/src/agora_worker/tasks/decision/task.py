from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Agent
from pydantic_ai.durable_exec.dbos import DBOSDurability

from agora_worker.tasks.base import Task


class DecisionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    text: str = Field(min_length=1)
    question: str = Field(min_length=1, description="A yes/no question about the supplied text.")


class DecisionAnswer(BaseModel):
    answer: bool = Field(description="Does the text satisfy the question in the instructions?")


class DecisionOutput(BaseModel):
    answer: bool
    probability_yes: float = Field(ge=0, le=1)


class DecisionTask(Task[DecisionInput, DecisionOutput]):
    id = "decide"
    description = "Answer a yes/no question about text with Jev and report its probability."
    input_model = DecisionInput
    output_model = DecisionOutput

    agent: ClassVar[Agent[DecisionInput, DecisionAnswer]] = Agent(
        "typesafe:jev-latest",
        name="agora_decide_v1",
        deps_type=DecisionInput,
        output_type=DecisionAnswer,
        defer_model_check=True,
        capabilities=[DBOSDurability()],
    )

    def run(self, inputs: DecisionInput) -> DecisionOutput:
        result = self.agent.run_sync(
            inputs.text,
            instructions=f"Answer this yes/no question about the supplied text: {inputs.question}",
            deps=inputs,
        )
        details = result.response.provider_details or {}
        confidence = float(details["confidence"]["answer"])
        return DecisionOutput(
            answer=result.output.answer,
            probability_yes=confidence if result.output.answer else 1 - confidence,
        )
