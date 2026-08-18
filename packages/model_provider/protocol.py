"""Structural interface used by Agent Runtime without vendor coupling."""

import json
from typing import Protocol, TypeVar

from pydantic import BaseModel

from packages.model_provider.errors import StructuredOutputError
from packages.model_provider.models import ChatMessage, LLMRequest, LLMResponse

OutputT = TypeVar("OutputT", bound=BaseModel)


class LLMProvider(Protocol):
    name: str

    def complete(self, request: LLMRequest) -> LLMResponse: ...

    def complete_structured(self, request: LLMRequest, output_schema: type[OutputT]) -> OutputT:
        """Complete a request and validate its JSON payload against ``output_schema``."""


class StructuredOutputMixin:
    """Shared JSON validation for real and deterministic providers."""

    def complete_structured(self, request: LLMRequest, output_schema: type[OutputT]) -> OutputT:
        output, _ = complete_structured_with_response(self, request, output_schema)
        return output


def complete_structured_with_response[StructuredOutputT: BaseModel](
    provider: LLMProvider,
    request: LLMRequest,
    output_schema: type[StructuredOutputT],
) -> tuple[StructuredOutputT, LLMResponse]:
    """Validate structured output while retaining usage/provider response metadata."""

    schema_instruction = json.dumps(output_schema.model_json_schema(), ensure_ascii=False)
    structured_request = request.model_copy(
        update={
            "messages": [
                *request.messages,
                ChatMessage(
                    role="system",
                    content=f"必须只输出满足以下 JSON Schema 的 JSON: {schema_instruction}",
                ),
            ]
        }
    )
    response = provider.complete(structured_request)
    try:
        payload = json.loads(response.content)
    except (TypeError, ValueError) as exc:
        raise StructuredOutputError("模型返回内容不是有效 JSON") from exc
    try:
        return output_schema.model_validate(payload), response
    except Exception as exc:
        raise StructuredOutputError(
            f"模型 JSON 不符合 {output_schema.__name__} 结构: {exc}"
        ) from exc
