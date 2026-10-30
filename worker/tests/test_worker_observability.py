from inspect import unwrap
from traceback import format_exception

import pytest
from dbos._context import DBOSContext
from dbos._tracer import dbos_tracer
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode
from pydantic import JsonValue

from agora_worker.workflows import WORKFLOW_NAME, execute

MARKER = "controlled-private-content-marker"


@pytest.mark.parametrize(
    "payload",
    [
        {"task": "generate", "inputs": {"prompt": [MARKER]}},
        {"task": "generate", "inputs": {"instructions": MARKER}},
        {"task": "generate", "inputs": {"prompt": "Hello", "extra": MARKER}},
        {"task": "generate", "inputs": {"prompt": "Hello"}, "extra": MARKER},
    ],
)
def test_invalid_task_data_is_excluded_from_dbos_traces(
    payload: dict[str, JsonValue], monkeypatch: pytest.MonkeyPatch
) -> None:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(dbos_tracer, "provider", provider)
    monkeypatch.setattr(dbos_tracer, "disable_otlp", False)
    # Exercise DBOS error spans without launching a database-backed runtime.
    context = DBOSContext()
    context.start_workflow("invalid-task-data-test", {"name": WORKFLOW_NAME})
    error: BaseException | None = None
    try:
        with pytest.raises(ValueError) as captured:
            unwrap(execute)(payload)
        error = captured.value
    finally:
        context.end_workflow(error)
        provider.shutdown()

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code == StatusCode.ERROR
    assert spans[0].status.description == "Invalid task data"
    assert MARKER not in spans[0].to_json()
    assert MARKER not in "".join(format_exception(captured.value))
