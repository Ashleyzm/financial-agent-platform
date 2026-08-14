"""Provider-neutral request and response models."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class LLMRequest(BaseModel):
    """A portable chat completion request understood by all providers."""

    model_config = ConfigDict(extra="forbid")

    messages: list[ChatMessage] = Field(min_length=1)
    model: str | None = None
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=1200, ge=1, le=16_384)
    timeout_seconds: float = Field(default=30.0, gt=0, le=300)


class LLMResponse(BaseModel):
    """Normalized response metadata, independent of a vendor SDK."""

    model_config = ConfigDict(extra="forbid")

    content: str
    provider: str
    model: str
    request_id: str | None = None
    usage: dict[str, Any] = Field(default_factory=dict)
