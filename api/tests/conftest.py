from collections.abc import Iterator
from unittest.mock import Mock

import logfire
import pytest
from fastapi import FastAPI
from pydantic import SecretStr

from agora_api.config import settings


@pytest.fixture(autouse=True)
def local_tracing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "logfire_token", SecretStr(""))
    logfire.configure(send_to_logfire=False, console=False, inspect_arguments=False)


@pytest.fixture
def app() -> Iterator[FastAPI]:
    from agora_api.api.deps import get_registry_connection
    from agora_api.main import app

    app.dependency_overrides.clear()
    connection = Mock()
    numbers = {
        "type": "object",
        "properties": {
            "left": {"type": "integer", "minimum": -1_000_000, "maximum": 1_000_000},
            "right": {"type": "integer", "minimum": -1_000_000, "maximum": 1_000_000},
            "double_positive": {"type": "boolean"},
            "divisor": {"type": "integer"},
        },
        "required": ["left", "right"],
        "additionalProperties": False,
    }
    connection.execute.return_value.fetchone.return_value = (
        [
            {
                "id": name,
                "description": "Test operation",
                "input_schema": numbers,
                "output_schema": {},
                "credentials": [],
                "constraints": [],
            }
            for name in ["add_then_scale", "divide_sum"]
        ],
    )
    app.dependency_overrides[get_registry_connection] = lambda: connection
    try:
        yield app
    finally:
        app.dependency_overrides.clear()
