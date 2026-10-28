from collections.abc import Iterator

import pytest
from fastapi import FastAPI


@pytest.fixture
def app() -> Iterator[FastAPI]:
    from agora_api.main import app

    app.dependency_overrides.clear()
    try:
        yield app
    finally:
        app.dependency_overrides.clear()
