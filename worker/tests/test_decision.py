import pytest
from pydantic import ValidationError
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from agora_worker.tasks.decision.task import DecisionInput, DecisionTask


@pytest.mark.parametrize("answer,confidence,probability", [(True, 0.8, 0.8), (False, 0.8, 0.2)])
def test_decision_preserves_probability(
    monkeypatch: pytest.MonkeyPatch, answer: bool, confidence: float, probability: float
) -> None:
    monkeypatch.setattr("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False)

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        assert info.output_tools
        assert "refund" in (info.instructions or "")
        return ModelResponse(
            parts=[ToolCallPart(info.output_tools[0].name, {"answer": answer})],
            provider_name="typesafe",
            provider_details={"confidence": {"answer": confidence}},
        )

    with DecisionTask.agent.override(model=FunctionModel(model)):
        result = DecisionTask().run(
            DecisionInput(text="Please give my money back", question="Is this a refund request?")
        )
    assert result.answer is answer
    assert result.probability_yes == pytest.approx(probability)


@pytest.mark.parametrize(
    "inputs",
    [
        {"text": "", "question": "Refund?"},
        {"text": "Hi"},
        {"text": "Hi", "question": "Refund?", "output_schema": {"type": "string"}},
    ],
)
def test_decision_rejects_invalid_inputs(inputs: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        DecisionInput.model_validate(inputs)
