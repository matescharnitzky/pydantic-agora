from pathlib import Path

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.workspaces import LocalWorkspaceBackend

from agora_worker.tasks.workspace.task import WorkspaceInput, WorkspaceTask


def test_workspace_reads_real_file_without_write_or_shell_tools(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False)
    (tmp_path / "note.txt").write_text("Copper Finch")

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        names = {tool.name for tool in info.function_tools}
        assert names == {"read_file", "list_directory", "find_files", "search_files"}
        if len(messages) == 1:
            return ModelResponse(parts=[ToolCallPart("read_file", {"path": "note.txt"})])
        returned = [p for m in messages for p in m.parts if isinstance(p, ToolReturnPart)]
        assert "Copper Finch" in str(returned[-1].content)
        return ModelResponse(parts=[TextPart("Copper Finch (note.txt)")])

    with WorkspaceTask.agent.override(
        model=FunctionModel(model), workspace=LocalWorkspaceBackend(tmp_path)
    ):
        result = WorkspaceTask().run(WorkspaceInput(prompt="What is the codename?"))
    assert result.output == "Copper Finch (note.txt)"
    assert result.files_requested == ["note.txt"]


@pytest.mark.parametrize("path", ["../outside.txt", "escape.txt"])
def test_workspace_rejects_paths_outside_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    monkeypatch.setattr("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False)
    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("PRIVATE-MARKER")
    (root / "escape.txt").symlink_to(outside)

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if len(messages) == 1:
            return ModelResponse(parts=[ToolCallPart("read_file", {"path": path})])
        assert "PRIVATE-MARKER" not in str(messages)
        return ModelResponse(parts=[TextPart("Access denied")])

    with WorkspaceTask.agent.override(
        model=FunctionModel(model), workspace=LocalWorkspaceBackend(root)
    ):
        assert WorkspaceTask().run(WorkspaceInput(prompt="Read outside")).output == "Access denied"


def test_workspace_searches_real_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False)
    (tmp_path / "note.txt").write_text("The codename is Copper Finch")

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if len(messages) == 1:
            return ModelResponse(parts=[ToolCallPart("search_files", {"pattern": "Copper"})])
        returned = [p for m in messages for p in m.parts if isinstance(p, ToolReturnPart)]
        assert "Copper Finch" in str(returned[-1].content)
        assert "note.txt" in str(returned[-1].content)
        return ModelResponse(parts=[TextPart("Found in note.txt")])

    with WorkspaceTask.agent.override(
        model=FunctionModel(model), workspace=LocalWorkspaceBackend(tmp_path)
    ):
        assert WorkspaceTask().run(WorkspaceInput(prompt="Search")).output == "Found in note.txt"


def test_missing_file_is_reported_to_model(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False)

    def model(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if len(messages) == 1:
            return ModelResponse(parts=[ToolCallPart("read_file", {"path": "missing.txt"})])
        returned = [p for m in messages for p in m.parts if isinstance(p, ToolReturnPart)]
        assert "not found" in str(returned[-1].content).lower()
        return ModelResponse(parts=[TextPart("File missing")])

    with WorkspaceTask.agent.override(
        model=FunctionModel(model), workspace=LocalWorkspaceBackend(tmp_path)
    ):
        result = WorkspaceTask().run(WorkspaceInput(prompt="Read missing.txt"))
    assert result.output == "File missing"
    assert result.files_requested == ["missing.txt"]
