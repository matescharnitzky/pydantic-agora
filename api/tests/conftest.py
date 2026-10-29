from collections.abc import Iterator

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
    from agora_api.main import app

    app.dependency_overrides.clear()
    try:
        yield app
    finally:
        app.dependency_overrides.clear()
