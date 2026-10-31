import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, cast

import pytest
from pydantic import JsonValue
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from agora_worker.models import OrchestrationRequest
from agora_worker.orchestrator.agent import create_agent, run_orchestration
from agora_worker.tasks.generation.task import GenerationTask


def code_model(code: str) -> FunctionModel:
    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if len(messages) == 1:
            assert [tool.name for tool in info.function_tools] == ["run_code"]
            return ModelResponse(parts=[ToolCallPart("run_code", {"code": code})])
        parts = [p for m in messages for p in m.parts if isinstance(p, ToolReturnPart)]
        return ModelResponse(parts=[TextPart(str(parts[-1].content))])

    return FunctionModel(respond)


def test_task_tool_contract_and_output_validation() -> None:
    tool = GenerationTask.as_tool(lambda task, inputs: {"output": inputs["prompt"]})
    assert tool.name == GenerationTask.id
    assert tool.tool_def.parameters_json_schema == GenerationTask.input_model.model_json_schema()
    assert tool.tool_def.return_schema == GenerationTask.output_model.model_json_schema()
    assert asyncio.run(
        cast(Callable[..., Coroutine[Any, Any, object]], tool.function)(prompt="hello")
    ) == {"output": "hello"}
    with pytest.raises(ValueError, match="Invalid task data"):
        asyncio.run(cast(Callable[..., Coroutine[Any, Any, object]], tool.function)(prompt=42))
    with pytest.raises(ValueError, match="Invalid task data"):
        asyncio.run(
            cast(
                Callable[..., Coroutine[Any, Any, object]],
                GenerationTask.as_tool(lambda task, inputs: {}).function,
            )(prompt="hello")
        )


def test_native_monty_branch_and_loop() -> None:
    calls: list[tuple[str, dict[str, JsonValue]]] = []

    def execute(task: str, inputs: dict[str, JsonValue]) -> dict[str, JsonValue]:
        calls.append((task, inputs))
        return {"output": inputs["prompt"]}

    agent = create_agent(execute)
    code = """data = supplied_data()
results = []
for document in data['documents']:
    if document != 'skip':
        results.append(generate(prompt=document)['output'])
results"""
    with agent.override(model=code_model(code)):
        result = run_orchestration(
            OrchestrationRequest(
                prompt="Process documents", data={"documents": ["first", "skip", "last"]}
            ),
            agent,
        )
    assert calls == [
        ("generate", {"prompt": "first", "instructions": ""}),
        ("generate", {"prompt": "last", "instructions": ""}),
    ]
    assert "first" in str(result) and "last" in str(result)


@pytest.mark.parametrize(
    "code",
    [
        "dummy()",
        "unknown()",
        "generate(prompt=42)",
        "generate(prompt='fail')",
        "import os\nos.environ['OPENAI_API_KEY']",
        "while True:\n    pass",
    ],
)
def test_native_monty_failures(code: str) -> None:
    def fail(task: str, inputs: dict[str, JsonValue]) -> dict[str, JsonValue]:
        raise ValueError("Task failed")

    agent = create_agent(fail)
    with (
        agent.override(model=code_model(code)),
        pytest.raises((UnexpectedModelBehavior, ValueError)),
    ):
        run_orchestration(OrchestrationRequest(prompt="Run"), agent)
