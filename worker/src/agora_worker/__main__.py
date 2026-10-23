import argparse
import logging
import signal
from threading import Event
from types import FrameType

import psycopg

from agora_worker.config import Settings

logger = logging.getLogger(__name__)


def check_database(settings: Settings) -> bool:
    try:
        with psycopg.connect(
            str(settings.database_url), connect_timeout=2, options="-c statement_timeout=2000"
        ) as connection:
            connection.execute("SELECT 1")
    except psycopg.Error:
        logger.warning("Database readiness check failed")
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Agora worker service")
    parser.add_argument("--check", action="store_true", help="Check database connectivity and exit")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = Settings()
    if not check_database(settings):
        return 1
    if args.check:
        return 0

    stopped = Event()

    def stop(_signum: int, _frame: FrameType | None) -> None:
        stopped.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    logger.info("Agora worker started; database ready; execution is not enabled")
    while not stopped.wait(timeout=10):
        if not check_database(settings):
            return 1
    logger.info("Agora worker stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
