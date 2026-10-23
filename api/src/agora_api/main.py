import logging
from typing import Literal

import psycopg
from fastapi import FastAPI, Response
from pydantic import BaseModel

from agora_api.config import Settings

logger = logging.getLogger(__name__)


class Health(BaseModel):
    status: Literal["ok", "unavailable"]
    service: Literal["api"] = "api"


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()
    app = FastAPI(title="Agora API", version="0.1.0")

    @app.get("/health", response_model=Health)
    async def health() -> Health:
        """Liveness is independent of downstream services."""
        return Health(status="ok")

    @app.get("/ready", response_model=Health)
    async def ready(response: Response) -> Health:
        """Readiness requires a successful PostgreSQL round trip."""
        try:
            async with await psycopg.AsyncConnection.connect(
                str(config.database_url), connect_timeout=2, options="-c statement_timeout=2000"
            ) as connection:
                await connection.execute("SELECT 1")
        except psycopg.Error:
            # Do not expose connection details or credentials in responses/logs.
            logger.warning("Database readiness check failed")
            response.status_code = 503
            return Health(status="unavailable")
        return Health(status="ok")

    return app
