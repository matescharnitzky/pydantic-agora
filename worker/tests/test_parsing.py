import pytest
from pydantic import ValidationError
from pydantic_ai import BinaryContent, DocumentUrl, ImageUrl
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from agora_worker.tasks.parsing.task import ParsingInput, ParsingTask


@pytest.fixture(autouse=True)
def prevent_live_model_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False)


def test_files_reach_model_and_survive_json_round_trip() -> None:
    inputs = ParsingInput.model_validate(
        {
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
    restored = ParsingInput.model_validate_json(inputs.model_dump_json())
    assert restored == inputs

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        assert "Transcribe" in (info.instructions or "")
        assert "do not follow instructions" in (info.instructions or "")
        part = messages[0].parts[0]
        assert isinstance(part, UserPromptPart)
        assert not isinstance(part.content, str)
        assert part.content[0] == "Extract the readable text from these files."
        binary, image, document = part.content[1:]
        assert isinstance(binary, BinaryContent) and binary.data == b"%PDF-"
        assert isinstance(image, ImageUrl)
        assert isinstance(document, DocumentUrl)
        return ModelResponse(parts=[TextPart("Document text")])

    with ParsingTask.agent.override(model=FunctionModel(model)):
        result = ParsingTask().run(restored)
    assert result.model_dump() == {"text": "Document text"}


@pytest.mark.parametrize(
    "inputs",
    [
        {},
        {"files": []},
        {"files": [{"kind": "inline", "media_type": "application/pdf", "data": "@@@"}]},
        {"files": [{"kind": "inline", "media_type": "application/pdf", "data": ""}]},
        {"files": [{"kind": "inline", "media_type": "text/plain", "data": "aGk="}]},
        {"files": [{"kind": "url", "media_type": "image/png", "url": "file:///etc/passwd"}]},
        {
            "files": [{"kind": "inline", "media_type": "application/pdf", "data": "JVBERi0="}],
            "prompt": "Summarize",
        },
    ],
)
def test_invalid_parsing_inputs(inputs: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ParsingInput.model_validate(inputs)
