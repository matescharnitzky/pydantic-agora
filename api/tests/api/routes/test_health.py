from fastapi.testclient import TestClient
from pydantic import SecretStr

from agora_api.core.config import Settings
from agora_api.main import create_app


def test_liveness_does_not_require_database() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api"}


def test_readiness_returns_service_unavailable_without_leaking_credentials() -> None:
    settings = Settings(
        postgres_host="127.0.0.1", postgres_port=1, postgres_password=SecretStr("secret")
    )
    client = TestClient(create_app(settings))
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "service": "api"}
    assert "secret" not in response.text
