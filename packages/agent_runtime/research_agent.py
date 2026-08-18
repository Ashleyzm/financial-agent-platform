"""Research Agent backed by a structured, provider-agnostic LLM call."""

from pydantic import BaseModel, Field, HttpUrl

from packages.agent_runtime.state import AgentState
from packages.contracts import EvidenceItem, EvidenceType, ModelUsage
from packages.model_provider import (
    ChatMessage,
    LLMProvider,
    LLMRequest,
    complete_structured_with_response,
)
from packages.model_provider.errors import LLMProviderError


class ResearchEvidence(BaseModel):
    """Small evidence shape that is safe for both Mock and real model output."""

    title: str = Field(min_length=1, max_length=300)
    source: str = Field(min_length=1, max_length=120)
    excerpt: str = Field(min_length=1, max_length=2000)
    relevance: float = Field(default=0.5, ge=0, le=1)
    url: HttpUrl | None = None


class ResearchOutput(BaseModel):
    """Versioned structured output consumed by downstream prediction and report nodes."""

    summary: str = Field(min_length=1, max_length=5000)
    thesis: str = Field(min_length=1, max_length=2000)
    catalysts: list[str] = Field(default_factory=list, max_length=10)
    risks: list[str] = Field(default_factory=list, max_length=10)
    confidence: float = Field(default=0.5, ge=0, le=1)
    evidence: list[ResearchEvidence] = Field(default_factory=list, max_length=20)


RESEARCH_SYSTEM_PROMPT = """你是金融研究 Agent。只输出符合给定 JSON Schema 的 JSON，不要 Markdown。
基于用户问题和已提供的市场快照，给出中性、可追溯的研究摘要。不要编造新闻、财报、价格或来源；没有真实证据时明确说明数据缺口。内容仅用于研究与教学，不构成投资建议。"""


def build_research_request(state: AgentState, *, timeout_seconds: float = 30.0) -> LLMRequest:
    request = state["request"]
    snapshot = state.get("market_snapshot")
    snapshot_text = snapshot.model_dump_json() if snapshot is not None else "暂无行情快照"
    existing_evidence = [item.model_dump(mode="json") for item in state["evidence"]]
    user_content = (
        f"标的: {request.symbol}\n市场: {request.market.value}\n"
        f"研究问题: {request.question}\n预测期限: {request.horizon_days} 天\n"
        f"市场快照: {snapshot_text}\n已有证据: {existing_evidence}"
    )
    return LLMRequest(
        messages=[
            ChatMessage(role="system", content=RESEARCH_SYSTEM_PROMPT),
            ChatMessage(role="user", content=user_content),
        ],
        timeout_seconds=timeout_seconds,
    )


def run_research_agent(
    state: AgentState,
    provider: LLMProvider,
    *,
    timeout_seconds: float = 30.0,
) -> None:
    """Call the provider and merge validated research output into shared AgentState."""

    try:
        output, response = complete_structured_with_response(
            provider,
            build_research_request(state, timeout_seconds=timeout_seconds),
            ResearchOutput,
        )
    except LLMProviderError:
        raise
    except Exception as exc:
        raise LLMProviderError(f"Research Agent 调用模型失败: {exc}") from exc

    state["research_summary"] = _render_summary(output)
    state["evidence"].extend(_to_contract_evidence(output))
    usage = response.usage
    input_tokens = int(usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0)
    output_tokens = int(usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0)
    total_tokens = int(usage.get("total_tokens", input_tokens + output_tokens) or 0)
    state["model_usage"] = ModelUsage(
        provider=response.provider,
        model=response.model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
    )


def _render_summary(output: ResearchOutput) -> str:
    sections = [output.summary, f"研究观点：{output.thesis}"]
    if output.catalysts:
        sections.append("潜在催化剂：" + "；".join(output.catalysts))
    if output.risks:
        sections.append("主要风险：" + "；".join(output.risks))
    sections.append(f"研究置信度：{output.confidence:.0%}")
    return "\n".join(sections)[:5000]


def _to_contract_evidence(output: ResearchOutput) -> list[EvidenceItem]:
    return [
        EvidenceItem(
            evidence_type=EvidenceType.RESEARCH,
            title=item.title,
            source=item.source,
            excerpt=item.excerpt,
            relevance=item.relevance,
            url=item.url,
            metadata={"agent": "research", "provider_output": True},
        )
        for item in output.evidence
    ]
