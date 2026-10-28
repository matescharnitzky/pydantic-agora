import os

import pytest
from pydantic import SecretStr

from agora_worker.config import Settings
from agora_worker.health import check_database


def test_readiness_fails_for_unreachable_database() -> None:
    settings = Settings(
        postgres_host="127.0.0.1", postgres_port=1, postgres_password=SecretStr("secret")
    )
    assert not check_database(settings)


@pytest.mark.integration
def test_readiness_connects_to_postgres() -> None:
    if not os.environ.get("POSTGRES_PASSWORD"):
        pytest.fail("POSTGRES_PASSWORD is required for database integration tests", pytrace=False)
    assert check_database(Settings())
