from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    database_url: PostgresDsn = PostgresDsn("postgresql://agora:agora-local@127.0.0.1:5432/agora")
