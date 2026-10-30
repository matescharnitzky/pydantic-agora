import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_database_readiness(app: FastAPI) -> None:
    if not os.environ.get("POSTGRES_PASSWORD"):
        pytest.fail("POSTGRES_PASSWORD is required for database integration tests", pytrace=False)
    response = TestClient(app).get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api"}


@pytest.mark.integration
def test_discovery_reads_published_worker_registry(app: FastAPI) -> None:
    from agora_api.api.deps import get_database_connection

    if not os.environ.get("POSTGRES_PASSWORD"):
        pytest.fail("POSTGRES_PASSWORD is required for database integration tests", pytrace=False)
    app.dependency_overrides.pop(get_database_connection)
    response = TestClient(app).get("/tasks")
    assert response.status_code == 200
    tasks = {item["id"]: item for item in response.json()}
    assert "generate" in tasks
    assert "prompt" in tasks["generate"]["input_schema"]["properties"]
    assert tasks["generate"]["output_schema"]["properties"]["output"]["type"] == "string"
    assert "add_then_scale" in tasks
