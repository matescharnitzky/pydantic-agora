import pytest
from pydantic import ValidationError
from pydantic_ai.models.decision import (
    ChoiceAnswer as NativeChoiceAnswer,
)
from pydantic_ai.models.decision import (
    ChoiceQuestion as NativeChoiceQuestion,
)
from pydantic_ai.models.decision import (
    DecisionModelSettings,
    DecisionRequest,
    DecisionResponse,
    NoulAnswer,
    NoulQuestion,
    ScoreAnswer,
    ScoreQuestion,
)
from pydantic_ai.models.typesafe import TypeSafeModel
from pydantic_ai.providers.typesafe import TypeSafeProvider

from agora_worker.tasks.decision.task import (
    BooleanAnswer,
    ChoiceAnswer,
    DecisionInput,
    DecisionOutput,
    DecisionTask,
    RubricAnswer,
)


@pytest.fixture
def jev(monkeypatch: pytest.MonkeyPatch) -> TypeSafeModel:
    # Tests replace decide() below: exercise upstream schema mapping without a provider request.
    monkeypatch.setattr("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False)
    monkeypatch.setattr("pydantic_ai.models.decision.check_allow_model_requests", lambda: None)
    return TypeSafeModel("jev-latest", provider=TypeSafeProvider(api_key="unit-test-unused"))


@pytest.mark.parametrize("probability", [0.0, 0.2, 0.5, 0.8, 1.0])
def test_boolean_uses_actual_yes_probability(
    monkeypatch: pytest.MonkeyPatch, jev: TypeSafeModel, probability: float
) -> None:
    async def decide(request: DecisionRequest, settings: DecisionModelSettings) -> DecisionResponse:
        assert isinstance(request.questions["q0"], NoulQuestion)
        return DecisionResponse(answers={"q0": NoulAnswer(noul=probability)}, model_name="jev-test")

    monkeypatch.setattr(jev, "decide", decide)
    inputs = DecisionInput.model_validate(
        {
            "text": "Please give my money back",
            "questions": {
                "refund_requested": {"type": "boolean", "question": "Is this a refund request?"}
            },
        }
    )
    with DecisionTask.agent.override(model=jev):
        result = DecisionTask().run(inputs)
    answer = result.answers["refund_requested"]
    assert isinstance(answer, BooleanAnswer)
    assert answer.value is (probability >= 0.5)
    assert answer.probability_yes == probability


def test_mixed_questions_use_native_decision_types_and_preserve_distributions(
    monkeypatch: pytest.MonkeyPatch,
    jev: TypeSafeModel,
) -> None:
    requests: list[DecisionRequest] = []

    async def decide(request: DecisionRequest, settings: DecisionModelSettings) -> DecisionResponse:
        requests.append(request)
        boolean, choice, rubric = request.questions.values()
        assert isinstance(boolean, NoulQuestion)
        assert isinstance(boolean.instructions, dict)
        assert boolean.instructions["question"] == "model_dump"
        assert isinstance(choice, NativeChoiceQuestion)
        assert set(choice.criteria) == {"billing", "delivery"}
        assert isinstance(choice.instructions, dict)
        assert choice.instructions["question"] == "Which team should handle this?"
        assert isinstance(rubric, ScoreQuestion)
        assert rubric.criteria == ["No impact", "Workaround available", "Cannot work"]
        return DecisionResponse(
            answers={
                "q0": NoulAnswer(noul=0.9),
                "q1": NativeChoiceAnswer(
                    choice="billing",
                    confidence=0.7,
                    probabilities={"billing": 0.9, "delivery": 0.1},
                ),
                "q2": ScoreAnswer(
                    score=1.6,
                    confidence=0.6,
                    probabilities={0: 0.1, 1: 0.2, 2: 0.7},
                ),
            },
            model_name="jev-test",
        )

    monkeypatch.setattr(jev, "decide", decide)
    inputs = DecisionInput.model_validate(
        {
            "text": "I cannot work until my billing issue is fixed.",
            "questions": {
                "model_dump": {"type": "boolean"},
                "category": {
                    "type": "choice",
                    "question": "Which team should handle this?",
                    "options": ["billing", "delivery"],
                },
                "urgency": {
                    "type": "rubric",
                    "levels": [
                        "No impact",
                        "Workaround available",
                        "Cannot work",
                    ],
                },
            },
        }
    )
    with DecisionTask.agent.override(model=jev):
        result = DecisionTask().run(inputs)
    assert len(requests) == 1
    category = result.answers["category"]
    assert isinstance(category, ChoiceAnswer)
    assert category.value == "billing"
    assert category.confidence == 0.7
    assert category.probabilities == {"billing": 0.9, "delivery": 0.1}
    urgency = result.answers["urgency"]
    assert isinstance(urgency, RubricAnswer)
    assert urgency.value == 2
    assert urgency.expected_score == 1.6
    assert urgency.confidence == 0.6
    assert urgency.probabilities == {"0": 0.1, "1": 0.2, "2": 0.7}
    assert DecisionOutput.model_validate_json(result.model_dump_json()) == result


@pytest.mark.parametrize(
    "questions",
    [
        {},
        {"": {"type": "boolean"}},
        {"summary": {"type": "string"}},
        {"category": {"type": "choice", "options": ["one"]}},
        {"category": {"type": "choice", "options": ["one", "one"]}},
        {"category": {"type": "choice", "options": ["one", ""]}},
        {"category": {"type": "choice", "options": [str(i) for i in range(256)]}},
        {"urgency": {"type": "rubric", "levels": ["Only one"]}},
        {"urgency": {"type": "rubric", "levels": ["First", ""]}},
        {"urgency": {"type": "rubric", "levels": [str(i) for i in range(11)]}},
        {"refund": {"type": "boolean", "output_schema": {}}},
    ],
)
def test_invalid_question_specs_fail_validation(questions: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        DecisionInput.model_validate({"text": "Hi", "questions": questions})


def test_text_is_required() -> None:
    with pytest.raises(ValidationError):
        DecisionInput.model_validate({"text": "", "questions": {"refund": {"type": "boolean"}}})
