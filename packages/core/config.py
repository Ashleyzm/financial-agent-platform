from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Financial Multi-Agent Platform"
    app_version: str = "0.1.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    web_port: int = 3000
    database_url: str = (
        "postgresql+psycopg://financial_agents:change-me@postgres:5432/financial_agents"
    )
    checkpoint_database_url: str | None = None
    redis_url: str = "redis://redis:6379/0"
    log_level: str = "INFO"
    market_data_provider: str = "mock"
    llm_provider: str = "mock"
    llm_api_key: str | None = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 2

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def resolved_checkpoint_database_url(self) -> str:
        """Use an explicit URL or reuse the application's Psycopg database URL."""

        return self.checkpoint_database_url or self.database_url.replace(
            "postgresql+psycopg://", "postgresql://", 1
        )

    @property
    def resolved_database_url(self) -> str:
        """Return a synchronous psycopg connection string for the task store."""

        return self.database_url.replace("postgresql+psycopg://", "postgresql://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
