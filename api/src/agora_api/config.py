from urllib.parse import quote

from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    logfire_token: SecretStr = SecretStr("")

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "postgres"
    postgres_user: str = "agora"
    postgres_password: SecretStr = SecretStr("")

    @property
    def database_url(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql",
            host=self.postgres_host,
            port=self.postgres_port,
            username=quote(self.postgres_user, safe=""),
            password=quote(self.postgres_password.get_secret_value(), safe=""),
            path=quote(self.postgres_db, safe=""),
        )

    @property
    def dbos_database_url(self) -> str:
        return str(self.database_url).replace("postgresql://", "postgresql+psycopg://", 1)


settings = Settings()
