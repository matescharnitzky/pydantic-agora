import pytest
from pydantic import ValidationError
from pydantic_ai.models import test

from agora_worker.tasks.generation.task import GenerationInput, GenerationTask


@pytest.fixture(autouse=True)
def prevent_live_model_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False)


def test_plain_text_generation() -> None:
    with GenerationTask.agent.override(model=test.TestModel(custom_output_text="Hello")):
        result = GenerationTask().run(
            GenerationInput(prompt="Say hello", instructions="Be concise")
        )
    assert result.output == "Hello"
    assert result.model_dump() == {"output": "Hello"}


@pytest.mark.parametrize(
    "inputs",
    [
        {"prompt": ""},
        {"prompt": 1},
        {"prompt": "Hi", "output_schema": {}},
        {"prompt": "Hi", "model": "another-model"},
        {"prompt": "Hi", "files": []},
    ],
)
def test_invalid_generation_inputs_fail_before_model_execution(inputs: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        GenerationInput.model_validate(inputs)
