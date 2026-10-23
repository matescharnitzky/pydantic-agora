import os

import pytest
from pydantic import PostgresDsn

from agora_worker.__main__ import check_database
from agora_worker.config import Settings


def test_readiness_fails_for_unreachable_database() -> None:
    settings = Settings(database_url=PostgresDsn("postgresql://agora:secret@127.0.0.1:1/missing"))
    assert not check_database(settings)


@pytest.mark.integration
@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL is required")
def test_readiness_connects_to_postgres() -> None:
    assert check_database(Settings())
