from urllib.parse import unquote, urlsplit

import pytest
from pydantic import SecretStr

from agora_api.config import Settings


@pytest.mark.parametrize("host", ["localhost", "postgres"])
def test_database_connection_preserves_credentials(host: str) -> None:
    password = "test:p@ss/word?#%"
    settings = Settings(
        postgres_host=host,
        postgres_user="test:user@local",
        postgres_password=SecretStr(password),
        postgres_db="test/database",
    )
    connection = urlsplit(str(settings.database_url))
    assert connection.hostname == host
    assert connection.port == 5432
    assert unquote(connection.username or "") == "test:user@local"
    assert unquote(connection.password or "") == password
    assert unquote(connection.path) == "/test/database"
    assert password not in repr(settings)
