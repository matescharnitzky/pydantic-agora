import os
from uuid import uuid4

import pytest
from dbos import DBOS, DBOSClient, DBOSConfig, SetWorkflowID
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.durable_exec.dbos import DBOSDurability
from pydantic_ai.models.test import TestModel
from test_orchestration import code_model

from agora_worker import workflows
from agora_worker.config import Settings
from agora_worker.orchestrator.agent import create_agent
from agora_worker.tasks.decision.task import DecisionInput, DecisionTask
from agora_worker.tasks.generation.task import GenerationInput, GenerationTask
from agora_worker.tasks.parsing.task import ParsingInput, ParsingOutput, ParsingTask
from agora_worker.workflows import WORKFLOW_NAME, orchestrate

pytestmark = pytest.mark.integration


def test_monty_calls_nested_task_workflows(monkeypatch: pytest.MonkeyPatch) -> None:
    if not os.environ.get("POSTGRES_PASSWORD"):
        pytest.fail("POSTGRES_PASSWORD is required for database integration tests", pytrace=False)
    config: DBOSConfig = {
        "name": "agora-worker",
        "system_database_url": Settings().dbos_database_url,
        "run_admin_server": False,
    }
    code = """data = supplied_data()
results = []
for document in data['documents']:
    if document != 'skip':
        text = parse(files=[{'kind': 'inline', 'media_type': 'image/png', 'data': 'aGk='}])['text']
        answer = decide(text=text, questions={'urgent': {'type': 'boolean'}})
        if answer['answers']['urgent']['value']:
            results.append(generate(prompt=text)['output'])
results"""
    agent = create_agent(
        lambda task, inputs: workflows.execute({"task": task, "inputs": inputs}),
        model=code_model(code),
        name="test_orchestrate_db",
    )
    monkeypatch.setattr(workflows, "orchestration_agent", agent)
    generation: Agent[GenerationInput, str] = Agent(
        TestModel(custom_output_text="reply"),
        name="test_generate_db",
        deps_type=GenerationInput,
        capabilities=[DBOSDurability(register_legacy_workflows=False)],
    )
    monkeypatch.setattr(GenerationTask, "agent", generation)
    parsing: Agent[ParsingInput, ParsingOutput] = Agent(
        TestModel(custom_output_args={"text": "urgent"}),
        name="test_parse_db",
        deps_type=ParsingInput,
        output_type=ParsingOutput,
        capabilities=[DBOSDurability(register_legacy_workflows=False)],
    )
    decision: Agent[DecisionInput, BaseModel] = Agent(
        TestModel(custom_output_args={"q0": 0.9}),
        name="test_decide_db",
        deps_type=DecisionInput,
        output_type=BaseModel,
        capabilities=[DBOSDurability(register_legacy_workflows=False)],
    )
    monkeypatch.setattr(ParsingTask, "agent", parsing)
    monkeypatch.setattr(DecisionTask, "agent", decision)
    failing_agent = create_agent(
        lambda task, inputs: workflows.execute({"task": task, "inputs": inputs}),
        model=code_model("dummy()"),
        name="test_orchestrate_failure_db",
    )
    DBOS(config=config)
    DBOS.launch()
    client = DBOSClient(system_database_url=Settings().dbos_database_url)
    try:
        run_id = str(uuid4())
        with SetWorkflowID(run_id):
            result = orchestrate(
                {"prompt": "Draft replies", "data": {"documents": ["first", "skip", "last"]}}
            )

        assert "reply" in str(result)
        children = client.list_workflows(parent_workflow_id=run_id)
        assert len(children) == 6
        assert all(child.name == WORKFLOW_NAME and child.status == "SUCCESS" for child in children)
        assert all(client.list_workflow_steps(child.workflow_id) for child in children)
        monkeypatch.setattr(workflows, "orchestration_agent", failing_agent)
        failed_id = str(uuid4())
        with SetWorkflowID(failed_id), pytest.raises(ValueError, match="Orchestration failed"):
            orchestrate({"prompt": "Call an internal task", "data": {}})
        status = client.retrieve_workflow(failed_id).get_status()
        assert status.status == "ERROR"
        assert client.list_workflows(parent_workflow_id=failed_id) == []
    finally:
        client.destroy()
        DBOS.destroy()
