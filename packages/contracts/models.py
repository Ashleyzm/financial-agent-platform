"""Pydantic models shared by the API, worker, agents, and web client."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from packages.contracts.enums import (
    AgentName,
    AgentStatus,
    ConfidenceLevel,
    EvidenceType,
    ForecastDirection,
    Market,
    RiskLevel,
    TaskStatus,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class ContractModel(BaseModel):
    """Strict base model used by every version 0.1 contract."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ForecastRequest(ContractModel):
    symbol: str = Field(min_length=1, max_length=15, pattern=r"^[A-Z0-9][A-Z0-9.\-]*$")
    market: Market = Market.US
    horizon_days: int = Field(default=5, ge=1, le=30)
    question: str = Field(default="分析该股票未来走势", min_length=2, max_length=500)
    include_news: bool = True
    include_financials: bool = True

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, value: Any) -> Any:
        return value.strip().upper() if isinstance(value, str) else value


class TaskReference(ContractModel):
    task_id: UUID = Field(default_factory=uuid4)
    trace_id: UUID = Field(default_factory=uuid4)
    status: TaskStatus = TaskStatus.QUEUED
    created_at: datetime = Field(default_factory=utc_now)


class ErrorDetail(ContractModel):
    code: str = Field(min_length=2, max_length=80)
    message: str = Field(min_length=1, max_length=1000)
    agent: AgentName | None = None
    module_code: str | None = Field(default=None, pattern=r"^[A-Z]{3}-\d{2}$")
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class AgentStep(ContractModel):
    agent: AgentName
    module_code: str = Field(default="AGT-01", pattern=r"^[A-Z]{3}-\d{2}$")
    status: AgentStatus = AgentStatus.PENDING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    summary: str | None = Field(default=None, max_length=500)
    error: ErrorDetail | None = None


class ModelUsage(ContractModel):
    provider: str | None = None
    model: str | None = None
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)


class EvidenceItem(ContractModel):
    evidence_id: UUID = Field(default_factory=uuid4)
    evidence_type: EvidenceType
    title: str = Field(min_length=1, max_length=300)
    source: str = Field(min_length=1, max_length=120)
    url: HttpUrl | None = None
    published_at: datetime | None = None
    excerpt: str = Field(min_length=1, max_length=2000)
    relevance: float = Field(ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MarketSnapshot(ContractModel):
    symbol: str = Field(min_length=1, max_length=15)
    price: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    as_of: datetime
    price_change_30d: float | None = None
    volatility_30d: float | None = Field(default=None, ge=0)
    volume: float | None = Field(default=None, ge=0)


class PredictionResult(ContractModel):
    horizon_days: int = Field(ge=1, le=30)
    direction: ForecastDirection
    upward_probability: float = Field(ge=0, le=1)
    expected_return: float | None = None
    model_name: str = Field(min_length=1, max_length=100)
    generated_at: datetime = Field(default_factory=utc_now)


class RiskAssessment(ContractModel):
    level: RiskLevel
    confidence: ConfidenceLevel
    volatility: float | None = Field(default=None, ge=0)
    max_drawdown: float | None = Field(default=None, le=0)
    factors: list[str] = Field(default_factory=list, max_length=20)


class ForecastReport(ContractModel):
    symbol: str = Field(min_length=1, max_length=15)
    market: Market
    generated_at: datetime = Field(default_factory=utc_now)
    prediction: PredictionResult
    research_summary: str = Field(min_length=1, max_length=5000)
    evidence: list[EvidenceItem] = Field(default_factory=list, max_length=50)
    risk: RiskAssessment
    disclaimer: str = "本报告仅用于研究与教学，不构成投资建议。"


class TaskDetail(TaskReference):
    request: ForecastRequest
    updated_at: datetime = Field(default_factory=utc_now)
    timeline: list[AgentStep] = Field(default_factory=list)
    report: ForecastReport | None = None
    error: ErrorDetail | None = None
    model_usage: ModelUsage = Field(default_factory=ModelUsage)


class APIError(ContractModel):
    code: str = Field(min_length=2, max_length=80)
    message: str = Field(min_length=1, max_length=1000)
    module_code: str = Field(pattern=r"^[A-Z]{3}-\d{2}$")
    trace_id: UUID
    task_id: UUID | None = None
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class APIErrorEnvelope(ContractModel):
    error: APIError


class CancelTaskResponse(ContractModel):
    task_id: UUID
    status: TaskStatus = TaskStatus.CANCELLED
    cancelled_at: datetime = Field(default_factory=utc_now)
