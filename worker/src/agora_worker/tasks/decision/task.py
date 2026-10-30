from collections.abc import Callable
from typing import Annotated, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, create_model, field_validator
from pydantic.fields import FieldInfo
from pydantic_ai import Agent, Choices
from pydantic_ai.durable_exec.dbos import DBOSDurability
from pydantic_ai.messages import ModelResponse

from agora_worker.tasks.base import Task

type AnswerField = tuple[type[object], FieldInfo]

type Probability = Annotated[float, Field(ge=0, le=1)]


class BooleanAnswer(BaseModel):
    type: Literal["boolean"] = "boolean"
    value: bool
    probability_yes: Probability


class ChoiceAnswer(BaseModel):
    type: Literal["choice"] = "choice"
    value: str
    confidence: Probability
    probabilities: dict[str, Probability]


class RubricAnswer(BaseModel):
    type: Literal["rubric"] = "rubric"
    value: int
    expected_score: float
    confidence: Probability
    probabilities: dict[str, Probability]


class BooleanQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    type: Literal["boolean"]
    question: str = ""

    def model_field(self, name: str) -> AnswerField:
        # A bounded float requests the actual yes probability, not the confidence margin.
        return float, Field(ge=0, le=1, description=self.question or name)

    def decode_answer(
        self, value: float | int | str, _response: ModelResponse, _key: str
    ) -> BooleanAnswer:
        probability = float(value)
        return BooleanAnswer(value=probability >= 0.5, probability_yes=probability)


class ChoiceQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    type: Literal["choice"]
    question: str = ""
    options: list[Annotated[str, Field(min_length=1)]] = Field(min_length=2, max_length=255)

    @field_validator("options")
    @classmethod
    def unique_options(cls, options: list[str]) -> list[str]:
        if len(set(options)) != len(options):
            raise ValueError("Choice options must be unique")
        return options

    def model_field(self, name: str) -> AnswerField:
        return Choices(self.options), Field(description=self.question or name)

    def decode_answer(
        self, value: float | int | str, response: ModelResponse, key: str
    ) -> ChoiceAnswer:
        details = response.provider_details or {}
        return ChoiceAnswer(
            value=str(value),
            confidence=details["confidence"][key],
            probabilities=details["probabilities"][key],
        )


class RubricQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    type: Literal["rubric"]
    question: str = ""
    levels: list[Annotated[str, Field(min_length=1)]] = Field(
        min_length=2,
        max_length=10,
        description="Descriptions of ordered levels, numbered from zero.",
    )

    def model_field(self, name: str) -> AnswerField:
        # Described integer levels starting at zero are the native decision-model rubric shape.
        return int, Field(
            ge=0,
            le=len(self.levels) - 1,
            description=self.question or name,
            json_schema_extra={
                "anyOf": [
                    {"const": level, "description": meaning}
                    for level, meaning in enumerate(self.levels)
                ]
            },
        )

    def decode_answer(
        self, value: float | int | str, response: ModelResponse, key: str
    ) -> RubricAnswer:
        details = response.provider_details or {}
        return RubricAnswer(
            value=int(value),
            expected_score=details["scores"][key],
            confidence=details["confidence"][key],
            probabilities=details["probabilities"][key],
        )


type Question = Annotated[
    BooleanQuestion | ChoiceQuestion | RubricQuestion, Field(discriminator="type")
]


class DecisionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    text: str = Field(min_length=1)
    questions: dict[Annotated[str, Field(min_length=1)], Question] = Field(min_length=1)


type Answer = Annotated[BooleanAnswer | ChoiceAnswer | RubricAnswer, Field(discriminator="type")]


class DecisionOutput(BaseModel):
    answers: dict[str, Answer]


def create_answer_model(questions: dict[str, Question]) -> type[BaseModel]:
    """Build Jev's output fields; internal names avoid collisions with BaseModel methods."""
    fields = {
        f"q{index}": question.model_field(name)
        for index, (name, question) in enumerate(questions.items())
    }
    # Generated qN names cannot bind create_model's reserved keyword arguments.
    model_factory: Callable[..., type[BaseModel]] = create_model
    return model_factory("DecisionAnswers", __config__=ConfigDict(extra="forbid"), **fields)


class DecisionTask(Task[DecisionInput, DecisionOutput]):
    id = "decide"
    description = "Answer named boolean, choice, and rubric questions with Jev."
    input_model = DecisionInput
    output_model = DecisionOutput

    agent: ClassVar[Agent[DecisionInput, BaseModel]] = Agent(
        "typesafe:jev-latest",
        name="decide",
        deps_type=DecisionInput,
        output_type=BaseModel,
        instructions="Answer the supplied questions using the provided text as evidence.",
        defer_model_check=True,
        capabilities=[DBOSDurability()],
    )

    def run(self, inputs: DecisionInput) -> DecisionOutput:
        result = self.agent.run_sync(
            inputs.text,
            output_type=create_answer_model(inputs.questions),
            deps=inputs,
        )
        values = result.output.model_dump(mode="json")
        answers = {
            name: question.decode_answer(values[f"q{index}"], result.response, f"q{index}")
            for index, (name, question) in enumerate(inputs.questions.items())
        }
        return DecisionOutput(answers=answers)
