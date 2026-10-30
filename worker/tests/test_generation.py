import pytest
from pydantic import JsonValue, ValidationError
from pydantic_ai import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.models import function, test

from agora_worker.generation import agent, generate
from agora_worker.models import GenerationInputs


@pytest.fixture(autouse=True)
def prevent_live_model_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False)


def test_plain_text_generation() -> None:
    with agent.override(model=test.TestModel(custom_output_text="Hello")):
        result = generate(GenerationInputs(prompt="Say hello", instructions="Be concise"))
    assert result.output == "Hello"


@pytest.mark.parametrize(
    ("schema", "output"),
    [
        ({"type": "object", "required": ["name"]}, {"name": "Ada"}),
        ({"type": "array", "items": {"type": "integer"}}, [1, 2]),
        ({"type": "boolean"}, True),
    ],
)
def test_caller_supplied_schema(schema: dict[str, JsonValue], output: JsonValue) -> None:
    with agent.override(model=test.TestModel(custom_output_args={"output": output})):
        result = generate(GenerationInputs(prompt="Generate", output_schema=schema))
    assert result.output == output


@pytest.mark.parametrize("correct_on_retry", [True, False])
def test_schema_constraints_are_validated_and_retried(correct_on_retry: bool) -> None:
    attempts = 0

    def respond(_messages: list[ModelMessage], info: function.AgentInfo) -> ModelResponse:
        nonlocal attempts
        attempts += 1
        assert info.output_tools
        value = 4 if attempts > 1 and correct_on_retry else -1
        return ModelResponse(
            parts=[ToolCallPart(info.output_tools[0].name, {"output": {"count": value}})]
        )

    inputs = GenerationInputs(
        prompt="Return a positive count",
        output_schema={
            "type": "object",
            "properties": {"count": {"type": "integer", "minimum": 1}},
            "required": ["count"],
        },
    )
    with agent.override(model=function.FunctionModel(respond)):
        if correct_on_retry:
            assert generate(inputs).output == {"count": 4}
        else:
            with pytest.raises(UnexpectedModelBehavior):
                generate(inputs)
    assert attempts == 2


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "imaginary"},
        {"$ref": "https://example.com/schema"},
        {"properties": {"value": {"$ref": "#/$defs/value"}}},
        {"$schema": "https://json-schema.org/draft-07/schema"},
    ],
)
def test_worker_rejects_invalid_or_unsupported_schemas(schema: dict[str, JsonValue]) -> None:
    with pytest.raises(ValidationError):
        GenerationInputs(prompt="Generate", output_schema=schema)
