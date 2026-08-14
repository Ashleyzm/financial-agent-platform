import json

import httpx
import pytest

from packages.agent_runtime import ResearchOutput
from packages.model_provider import (
    ChatMessage,
    LLMRequest,
    LLMTimeoutError,
    MockLLMProvider,
    OpenAICompatibleProvider,
    StructuredOutputError,
    create_model_provider,
)


def test_mock_provider_returns_valid_structured_output() -> None:
    provider = MockLLMProvider()
    request = LLMRequest(messages=[ChatMessage(role="user", content="Research NVDA")])

    result = provider.complete_structured(request, ResearchOutput)

    assert result.summary.startswith("Mock Research Agent")
    assert result.evidence[0].source == "mock-llm"


def test_mock_provider_reports_timeout_with_retry_hint() -> None:
    provider = MockLLMProvider(delay_seconds=1)
    request = LLMRequest(
        messages=[ChatMessage(role="user", content="Research NVDA")], timeout_seconds=0.01
    )

    with pytest.raises(LLMTimeoutError) as error:
        provider.complete(request)

    assert error.value.code == "llm_timeout"
    assert error.value.retryable is True


def test_invalid_structured_output_has_stable_error() -> None:
    provider = MockLLMProvider(response="not-json")
    request = LLMRequest(messages=[ChatMessage(role="user", content="Research NVDA")])

    with pytest.raises(StructuredOutputError) as error:
        provider.complete_structured(request, ResearchOutput)

    assert error.value.code == "llm_structured_output_invalid"


def test_openai_compatible_provider_normalizes_response(monkeypatch) -> None:
    captured: dict = {}

    class FakeClient:
        def __init__(self, **kwargs) -> None:
            captured["client"] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def post(self, path, *, json, headers):
            captured.update(path=path, json=json, headers=headers)
            return httpx.Response(
                200,
                json={
                    "id": "req-123",
                    "model": "real-model",
                    "choices": [{"message": {"content": "{\"ok\": true}"}}],
                    "usage": {"total_tokens": 10},
                },
            )

    monkeypatch.setattr(httpx, "Client", FakeClient)
    provider = OpenAICompatibleProvider(api_key="test-key", model="real-model")
    response = provider.complete(
        LLMRequest(messages=[ChatMessage(role="user", content="hello")], timeout_seconds=8)
    )

    assert json.loads(response.content) == {"ok": True}
    assert response.provider == "openai-compatible"
    assert captured["path"] == "chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["client"]["timeout"] == 8


def test_provider_factory_defaults_to_mock() -> None:
    provider = create_model_provider(env={})

    assert provider.name == "mock"
