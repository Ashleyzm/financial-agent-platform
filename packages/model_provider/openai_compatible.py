"""OpenAI-compatible Chat Completions provider.

The implementation uses the HTTP contract directly so it works with OpenAI,
vLLM, Ollama-compatible gateways, and other providers without a vendor SDK.
"""

from typing import Any

import httpx

from packages.model_provider.errors import LLMProviderError, LLMResponseError, LLMTimeoutError
from packages.model_provider.models import LLMRequest, LLMResponse
from packages.model_provider.protocol import StructuredOutputMixin


class OpenAICompatibleProvider(StructuredOutputMixin):
    name = "openai-compatible"

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        max_retries: int = 2,
    ) -> None:
        if not api_key:
            raise ValueError("OpenAI-compatible provider 需要 LLM_API_KEY 或 OPENAI_API_KEY")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.max_retries = max(0, max_retries)

    def complete(self, request: LLMRequest) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": request.model or self.model,
            "messages": [message.model_dump() for message in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(
                    base_url=self.base_url, timeout=request.timeout_seconds
                ) as client:
                    response = client.post("chat/completions", json=payload, headers=headers)
                if response.status_code >= 500 and attempt < self.max_retries:
                    continue
                if response.status_code >= 400:
                    raise LLMResponseError(
                        f"模型服务返回 HTTP {response.status_code}: {response.text[:500]}",
                        retryable=response.status_code >= 500,
                    )
                data = response.json()
                content = _extract_content(data)
                return LLMResponse(
                    content=content,
                    provider=self.name,
                    model=str(data.get("model", payload["model"])),
                    request_id=data.get("id"),
                    usage=data.get("usage") or {},
                )
            except httpx.TimeoutException as exc:
                raise LLMTimeoutError("模型请求超时") from exc
            except LLMResponseError:
                raise
            except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
        raise LLMProviderError(f"模型请求失败: {last_error}") from last_error


def _extract_content(data: dict[str, Any]) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMResponseError("模型响应缺少 choices[0].message.content") from exc
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = [item.get("text", "") for item in content if isinstance(item, dict)]
        return "".join(text_parts)
    raise LLMResponseError("模型响应 content 类型不受支持")
