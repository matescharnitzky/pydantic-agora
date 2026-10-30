import logging

import psycopg

from agora_worker.config import Settings

logger = logging.getLogger(__name__)


def check_database(settings: Settings) -> bool:
    """Probe PostgreSQL with connection and query timeouts, returning False on database errors."""
    try:
        with psycopg.connect(
            str(settings.database_url), connect_timeout=2, options="-c statement_timeout=2000"
        ) as connection:
            connection.execute("SELECT 1")
    except psycopg.Error:
        logger.warning("Database readiness check failed")
        return False
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raise SystemExit(0 if check_database(Settings()) else 1)
