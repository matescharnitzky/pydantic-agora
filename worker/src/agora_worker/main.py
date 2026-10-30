import logging
import signal
from threading import Event
from types import FrameType

import logfire
from dbos import DBOS, DBOSConfig

from agora_worker import workflows
from agora_worker.config import Settings

logger = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = Settings()

    stopped = Event()

    def stop(_signum: int, _frame: FrameType | None) -> None:
        stopped.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    logfire_token = settings.logfire_token.get_secret_value()
    logfire.configure(
        service_name="agora-worker",
        token=logfire_token or None,
        send_to_logfire=bool(logfire_token),
        console=False,
        inspect_arguments=False,
        data_dir="/tmp/agora-logfire-worker",
    )
    logfire.instrument_pydantic_ai(include_content=False, include_binary_content=False)
    config: DBOSConfig = {
        "name": "agora-worker",
        "system_database_url": settings.dbos_database_url,
        "run_admin_server": False,
        "enable_otlp": True,
    }
    DBOS(config=config)
    try:
        DBOS.launch()
        DBOS.register_queue(workflows.QUEUE_NAME, worker_concurrency=4)
        logger.info("Agora worker started; durable workflow enabled")
        stopped.wait()
    finally:
        DBOS.destroy()
    logger.info("Agora worker stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
