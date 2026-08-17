"""Stable error types exposed by every model provider."""


class LLMProviderError(RuntimeError):
    """Base error with a stable code and retry hint for agent timelines."""

    code = "llm_provider_error"
    retryable = False

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        retryable: bool | None = None,
    ) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code
        if retryable is not None:
            self.retryable = retryable


class LLMTimeoutError(LLMProviderError):
    code = "llm_timeout"
    retryable = True


class LLMResponseError(LLMProviderError):
    code = "llm_response_error"
    retryable = True


class StructuredOutputError(LLMProviderError):
    code = "llm_structured_output_invalid"
    retryable = False
