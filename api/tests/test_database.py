import os

import pytest
from fastapi.testclient import TestClient

from agora_api.main import create_app


@pytest.mark.integration
def test_database_readiness() -> None:
    if not os.environ.get("POSTGRES_PASSWORD"):
        pytest.fail("POSTGRES_PASSWORD is required for database integration tests", pytrace=False)
    response = TestClient(create_app()).get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api"}
