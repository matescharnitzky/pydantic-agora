import pytest
from pydantic_ai.messages import (
    Citation,
    ContentCitationAnchor,
    ModelMessage,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    WebCitationSource,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from agora_worker.tasks.web.task import WebInput, WebOutput, WebTask


def test_native_citation_anchors_survive_persistence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False)
    citation = Citation(
        sources=[WebCitationSource(url="https://example.com", title="Example")],
        anchor=ContentCitationAnchor(start=0, end=4),
    )

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        assert [tool.name for tool in info.function_tools] == ["web_fetch"]
        return ModelResponse(parts=[TextPart("Fact", citations=[citation]), TextPart("More")])

    with WebTask.agent.override(model=FunctionModel(model)):
        result = WebTask().run(WebInput(prompt="Research"))
    restored = WebOutput.model_validate_json(result.model_dump_json())
    assert restored.text_parts[0].citations == [citation]
    assert restored.text_parts[0].text == "Fact"
    assert restored.text_parts[1].text == "More"
    assert restored.fetched_pages == []


def test_worker_fetch_returns_source_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    from pydantic_ai import Tool

    monkeypatch.setattr("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False)

    def web_fetch(url: str) -> dict[str, str]:
        return {"url": url, "title": "Example", "content": "A fact"}

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if len(messages) == 1:
            return ModelResponse(parts=[ToolCallPart("web_fetch", {"url": "https://example.com"})])
        returned = [p for m in messages for p in m.parts if isinstance(p, ToolReturnPart)]
        assert "A fact" in str(returned[-1].content)
        return ModelResponse(parts=[TextPart("A fact")])

    with WebTask.agent.override(model=FunctionModel(model), tools=[Tool(web_fetch)]):
        result = WebTask().run(WebInput(prompt="Read example.com"))
    assert result.fetched_pages[0].model_dump() == {
        "url": "https://example.com",
        "title": "Example",
    }
    assert result.text_parts[0].citations == []


def test_fetch_rejects_private_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False)

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if len(messages) == 1:
            return ModelResponse(parts=[ToolCallPart("web_fetch", {"url": "http://127.0.0.1"})])
        retries = [
            p
            for m in messages
            for p in m.parts
            if isinstance(p, ToolReturnPart) and p.outcome == "retried"
        ]
        assert retries
        assert "Failed to fetch" in str(retries[-1].content)
        return ModelResponse(parts=[TextPart("Cannot fetch private URL")])

    with WebTask.agent.override(model=FunctionModel(model)):
        result = WebTask().run(WebInput(prompt="Read localhost"))
    assert result.fetched_pages == []
    assert result.output == "Cannot fetch private URL"


def test_citations_before_a_function_tool_call_are_preserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pydantic_ai import Tool

    monkeypatch.setattr("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False)
    citation = Citation(sources=[WebCitationSource(url="https://python.org")])

    def web_fetch(url: str) -> dict[str, str]:
        return {"url": url, "title": "Example", "content": "A fact"}

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if len(messages) == 1:
            return ModelResponse(
                parts=[
                    TextPart("Python website", citations=[citation]),
                    ToolCallPart("web_fetch", {"url": "https://example.com"}),
                ]
            )
        return ModelResponse(parts=[TextPart("Example")])

    with WebTask.agent.override(model=FunctionModel(model), tools=[Tool(web_fetch)]):
        result = WebTask().run(WebInput(prompt="Search then fetch"))
    assert result.text_parts[0].citations == [citation]
    assert result.text_parts[1].text == "Example"
