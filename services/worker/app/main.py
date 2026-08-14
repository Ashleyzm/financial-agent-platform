import logging
import time

from packages.core.config import settings

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("worker")


def run() -> None:
    logger.info("worker_started version=%s environment=%s", settings.app_version, settings.app_env)
    while True:
        time.sleep(30)
        logger.info("worker_heartbeat")


if __name__ == "__main__":
    run()
