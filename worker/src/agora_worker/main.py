import logging
import signal
from threading import Event
from types import FrameType

from dbos import DBOS, DBOSConfig, DBOSPortableJSONSerializer

from agora_worker import workflows
from agora_worker.config import Settings
from agora_worker.observability import configure_observability

logger = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = Settings()

    stopped = Event()

    def stop(_signum: int, _frame: FrameType | None) -> None:
        stopped.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    configure_observability(settings)
    config: DBOSConfig = {
        "name": "agora-worker",
        "system_database_url": settings.dbos_database_url,
        "run_admin_server": False,
        "enable_otlp": True,
        "otlp_traces_endpoints": [],
        "otlp_logs_endpoints": [],
        "serializer": DBOSPortableJSONSerializer(),
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
