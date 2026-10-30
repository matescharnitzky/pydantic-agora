from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Agent
from pydantic_ai.capabilities import LocalWorkspace
from pydantic_ai.durable_exec.dbos import DBOSDurability
from pydantic_ai_harness import FileSystem
from pydantic_ai_harness.filesystem import ReadFileCallPart

from agora_worker.tasks.base import Task


class WorkspaceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    prompt: str = Field(min_length=1)


class WorkspaceOutput(BaseModel):
    output: str
    files_requested: list[str]


class WorkspaceTask(Task[WorkspaceInput, WorkspaceOutput]):
    """Answer using read-only tools against the worker's mounted /workspace directory."""

    id = "workspace"
    description = "Answer questions using read, list, and search tools in the mounted workspace."
    input_model = WorkspaceInput
    output_model = WorkspaceOutput

    agent: ClassVar[Agent[WorkspaceInput, str]] = Agent(
        "openai-responses:gpt-5-mini",
        name="workspace",
        deps_type=WorkspaceInput,
        output_type=str,
        instructions="Use the workspace tools to answer. Cite file paths in your answer.",
        defer_model_check=True,
        capabilities=[
            DBOSDurability(),
            LocalWorkspace("/workspace", read_only=True),
            FileSystem(
                read_only=True,
                tools=["read_file", "list_directory", "find_files", "search_files"],
            ),
        ],
    )

    def run(self, inputs: WorkspaceInput) -> WorkspaceOutput:
        """Run the agent and report requested read paths once, in first-request order.

        Paths reflect read requests, including unsuccessful ones, rather than all files
        discovered by list or search tools.
        """
        result = self.agent.run_sync(inputs.prompt, deps=inputs)
        paths = [
            args["path"]
            for message in result.all_messages()
            for part in message.parts
            if isinstance(part, ReadFileCallPart) and (args := part.typed_args) is not None
        ]
        return WorkspaceOutput(output=result.output, files_requested=list(dict.fromkeys(paths)))
