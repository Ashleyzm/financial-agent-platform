from fastapi import FastAPI

from packages.core.config import settings
from services.api.app.tasks import router as tasks_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="金融多智能体平台 API",
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
