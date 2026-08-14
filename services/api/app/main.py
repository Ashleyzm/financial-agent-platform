import os
from contextlib import asynccontextmanager

os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")

from fastapi import FastAPI
from langgraph.checkpoint.postgres import PostgresSaver

from packages.agent_runtime import LangGraphWorkflowRunner, create_in_memory_runner
from packages.core.config import settings
from packages.financial_data import AkShareProvider
from services.api.app.task_service import task_service
from services.api.app.tasks import router as tasks_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create checkpoint tables and keep the PostgreSQL connection alive."""

    with PostgresSaver.from_conn_string(settings.resolved_checkpoint_database_url) as checkpointer:
        checkpointer.setup()
        task_service.set_runner(
            LangGraphWorkflowRunner(checkpointer, market_data_provider=AkShareProvider())
        )
        try:
            yield
        finally:
            task_service.set_runner(create_in_memory_runner())


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="金融多智能体平台 API",
    lifespan=lifespan,
)

app.include_router(tasks_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "api",
        "version": settings.app_version,
        "environment": settings.app_env,
    }
