import logging

import psycopg
from fastapi import APIRouter, Response

from agora_api.api.deps import SettingsDep
from agora_api.models import Health

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", response_model=Health)
async def health() -> Health:
    """Liveness is independent of downstream services."""
    return Health(status="ok")


@router.get("/ready", response_model=Health)
async def ready(response: Response, settings: SettingsDep) -> Health:
    """Readiness requires a successful PostgreSQL round trip."""
    try:
        async with await psycopg.AsyncConnection.connect(
            str(settings.database_url), connect_timeout=2, options="-c statement_timeout=2000"
        ) as connection:
            await connection.execute("SELECT 1")
    except psycopg.Error:
        # Do not expose connection details or credentials in responses/logs.
        logger.warning("Database readiness check failed")
        response.status_code = 503
        return Health(status="unavailable")
    return Health(status="ok")
