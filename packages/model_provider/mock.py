"""Deterministic LLM provider for local development and CI."""

import json
from time import sleep
from typing import Any

from packages.model_provider.errors import LLMProviderError, LLMTimeoutError
from packages.model_provider.models import LLMRequest, LLMResponse
from packages.model_provider.protocol import StructuredOutputMixin


class MockLLMProvider(StructuredOutputMixin):
    """Return a predictable structured research response without network access."""

    name = "mock"

    def __init__(
        self,
        *,
        response: dict[str, Any] | str | None = None,
        delay_seconds: float = 0,
        fail_with: Exception | None = None,
    ) -> None:
        self.response = response
        self.delay_seconds = delay_seconds
        self.fail_with = fail_with

    def complete(self, request: LLMRequest) -> LLMResponse:
        if self.fail_with is not None:
            if isinstance(self.fail_with, LLMProviderError):
                raise self.fail_with
            raise LLMProviderError(str(self.fail_with)) from self.fail_with
        if self.delay_seconds > request.timeout_seconds:
            message = (
                f"Mock provider 延迟 {self.delay_seconds:.2f}s "
                f"超过超时 {request.timeout_seconds:.2f}s"
            )
            raise LLMTimeoutError(message)
        if self.delay_seconds:
            sleep(self.delay_seconds)
        default_payload = {
            "summary": "Mock Research Agent 已完成结构化研究，等待真实新闻与财报 Provider。",
            "thesis": "当前仅用于验证 Agent Runtime 链路，不应据此进行交易决策。",
            "catalysts": ["真实数据接入后替换此占位结果"],
            "risks": ["模型与外部数据尚未在 Mock 模式下验证"],
            "confidence": 0.35,
            "evidence": [
                {
                    "title": "Mock research evidence",
                    "source": "mock-llm",
                    "excerpt": "Deterministic evidence for local workflow verification.",
                    "relevance": 0.5,
                }
            ],
        }
        content = self.response if self.response is not None else default_payload
        if isinstance(content, dict):
            content = json.dumps(content, ensure_ascii=False)
        return LLMResponse(
            content=content,
            provider=self.name,
            model=request.model or "mock-research-v0.1",
            request_id="mock-request",
            usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        )
