"""Environment-driven provider construction for API and worker processes."""

import os
from collections.abc import Mapping

from packages.model_provider.mock import MockLLMProvider
from packages.model_provider.openai_compatible import OpenAICompatibleProvider
from packages.model_provider.protocol import LLMProvider


def create_model_provider(
    *,
    provider: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    max_retries: int | None = None,
    env: Mapping[str, str] | None = None,
) -> LLMProvider:
    """Create Mock by default, or an OpenAI-compatible provider from settings."""

    values = env or os.environ
    selected = (provider or values.get("LLM_PROVIDER", "mock")).strip().lower()
    if selected == "mock":
        return MockLLMProvider()
    if selected in {"openai", "openai-compatible", "openai_compatible"}:
        return OpenAICompatibleProvider(
            api_key=api_key or values.get("LLM_API_KEY") or values.get("OPENAI_API_KEY"),
            model=model or values.get("LLM_MODEL", "gpt-4o-mini"),
            base_url=base_url or values.get("LLM_BASE_URL", "https://api.openai.com/v1"),
            max_retries=(
                max_retries if max_retries is not None else int(values.get("LLM_MAX_RETRIES", "2"))
            ),
        )
    raise ValueError(f"不支持的 LLM_PROVIDER: {selected}")
