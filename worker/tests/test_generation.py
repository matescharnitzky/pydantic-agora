import pytest
from pydantic import ValidationError
from pydantic_ai import BinaryContent, DocumentUrl, ImageUrl
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models import test
from pydantic_ai.models.function import AgentInfo, FunctionModel

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
    ],
)
def test_invalid_generation_inputs_fail_before_model_execution(inputs: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        GenerationInput.model_validate(inputs)


def test_files_reach_model_and_survive_json_round_trip() -> None:
    inputs = GenerationInput.model_validate(
        {
            "prompt": "Read these",
            "files": [
                {"kind": "inline", "media_type": "application/pdf", "data": "JVBERi0="},
                {"kind": "url", "media_type": "image/png", "url": "https://example.com/a.png"},
                {
                    "kind": "url",
                    "media_type": "application/pdf",
                    "url": "https://example.com/a.pdf",
                },
            ],
        }
    )
    restored = GenerationInput.model_validate_json(inputs.model_dump_json())
    assert restored == inputs

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        part = messages[0].parts[0]
        assert isinstance(part, UserPromptPart)
        assert not isinstance(part.content, str)
        assert part.content[0] == "Read these"
        binary, image, document = part.content[1:]
        assert isinstance(binary, BinaryContent) and binary.data == b"%PDF-"
        assert isinstance(image, ImageUrl)
        assert isinstance(document, DocumentUrl)
        return ModelResponse(parts=[TextPart("Read")])

    with GenerationTask.agent.override(model=FunctionModel(model)):
        assert GenerationTask().run(restored).output == "Read"


@pytest.mark.parametrize(
    "file",
    [
        {"kind": "inline", "media_type": "application/pdf", "data": "@@@"},
        {"kind": "inline", "media_type": "application/pdf", "data": ""},
        {"kind": "inline", "media_type": "text/plain", "data": "aGk="},
        {"kind": "url", "media_type": "image/png", "url": "file:///etc/passwd"},
    ],
)
def test_invalid_files(file: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        GenerationInput.model_validate({"prompt": "Read", "files": [file]})
