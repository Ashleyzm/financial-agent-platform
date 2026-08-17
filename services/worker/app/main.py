import logging

from langgraph.checkpoint.postgres import PostgresSaver

from packages.agent_runtime import LangGraphWorkflowRunner
from packages.contracts import ErrorDetail, TaskStatus, utc_now
from packages.core.config import settings
from packages.financial_data import AkShareProvider
from packages.task_store import PostgresTaskStore, RedisTaskQueue
from packages.task_store.base import InvalidTaskTransitionError, TaskNotFoundError

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("worker")


def run() -> None:
    store = PostgresTaskStore(settings.resolved_database_url)
    queue = RedisTaskQueue(settings.redis_url)
    logger.info(
        "worker_started version=%s environment=%s",
        settings.app_version,
        settings.app_env,
    )
    try:
        with PostgresSaver.from_conn_string(
            settings.resolved_checkpoint_database_url
        ) as checkpointer:
            checkpointer.setup()
            runner = LangGraphWorkflowRunner(
                checkpointer,
                market_data_provider=AkShareProvider(),
            )
            logger.info("worker_ready")
            while True:
                task_id = queue.dequeue(timeout=5.0)
                if task_id is None:
                    continue

                logger.info("worker_task_received task_id=%s", task_id)
                try:
                    state = store.claim_for_run(task_id)
                except (TaskNotFoundError, InvalidTaskTransitionError) as exc:
                    logger.warning(
                        "worker_task_skipped task_id=%s reason=%s",
                        task_id,
                        exc,
                    )
                    continue

                store.save(state)

                try:
                    state = runner(state)
                except Exception as exc:
                    logger.exception("worker_task_failed task_id=%s", task_id)
                    state = _mark_failed(state, exc)

                store.save(state)
                logger.info(
                    "worker_task_finished task_id=%s status=%s",
                    task_id,
                    state["status"].value,
                )
    finally:
        store.close()
        queue.close()


def _mark_failed(state, exc: Exception):
    state["status"] = TaskStatus.FAILED
    state["current_agent"] = None
    state["updated_at"] = utc_now()
    state["errors"].append(
        ErrorDetail(
            code="worker_execution_failed",
            message=str(exc),
            retryable=False,
        )
    )
    return state


if __name__ == "__main__":
    run()
