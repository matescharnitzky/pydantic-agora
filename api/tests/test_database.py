import os

import pytest
from fastapi.testclient import TestClient

from agora_api.main import create_app


@pytest.mark.integration
@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL is required")
def test_database_readiness() -> None:
    response = TestClient(create_app()).get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api"}
