"""Versioned risk-decision contracts owned by the Risk Agent (AGT-03/AGT-06)."""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from packages.contracts.models import ContractModel, EvidenceItem


class RiskDecisionLabel(StrEnum):
    NORMAL_RESEARCH = "normal_research"
    CAUTIOUS_WATCH = "cautious_watch"
    STAGE_AVOID = "stage_avoid"


class RiskExposureBand(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class HumanReviewStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class HumanReview(ContractModel):
    required: bool = False
    status: HumanReviewStatus = HumanReviewStatus.NOT_REQUIRED
    reviewer: str | None = Field(default=None, max_length=120)
    comment: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_status(self) -> "HumanReview":
        if self.required and self.status is HumanReviewStatus.NOT_REQUIRED:
            raise ValueError("required=true 时人工复核状态不能为 not_required")
        if not self.required and self.status is not HumanReviewStatus.NOT_REQUIRED:
            raise ValueError("required=false 时人工复核状态必须为 not_required")
        return self


class TechnicalRiskInput(ContractModel):
    """Normalized daily technical/market risk inputs."""

    symbol: str = Field(min_length=1, max_length=15)
    as_of: datetime
    trend_risk: float = Field(ge=0, le=100)
    drawdown_risk: float = Field(ge=0, le=100)
    volatility_risk: float = Field(ge=0, le=100)
    liquidity_risk: float = Field(ge=0, le=100)
    data_quality_risk: float = Field(ge=0, le=100)
    evidence: list[EvidenceItem] = Field(default_factory=list, max_length=20)
    provider_version: str = Field(default="unknown", min_length=1, max_length=80)


class TechnicalRiskOutput(ContractModel):
    """Deterministic output of the technical risk Agent."""

    module_code: str = Field(default="AGT-03", pattern=r"^[A-Z]{3}-\d{2}$")
    symbol: str = Field(min_length=1, max_length=15)
    as_of: datetime
    technical_score: float = Field(ge=0, le=100)
    exposure_band: RiskExposureBand
    factor_scores: dict[str, float] = Field(min_length=1)
    rationale: str = Field(min_length=1, max_length=2000)
    invalidators: list[str] = Field(default_factory=list, max_length=10)
    evidence: list[EvidenceItem] = Field(default_factory=list, max_length=20)
    human_review: HumanReview = Field(default_factory=HumanReview)
    versions: dict[str, str] = Field(default_factory=dict)


class RiskDecision(ContractModel):
    """Cross-engine RiskDecision v0.2 contract."""

    decision: RiskDecisionLabel
    as_of: datetime
    technical_score: float | None = Field(default=None, ge=0, le=100)
    event_score: float | None = Field(default=None, ge=0, le=100)
    industry_score: float | None = Field(default=None, ge=0, le=100)
    aggregate_score: float = Field(ge=0, le=100)
    risk_exposure_band: RiskExposureBand
    hard_veto: bool = False
    veto_reasons: list[str] = Field(default_factory=list, max_length=10)
    conflicts: list[str] = Field(default_factory=list, max_length=10)
    rationale: str = Field(min_length=1, max_length=3000)
    invalidators: list[str] = Field(default_factory=list, max_length=10)
    evidence: list[EvidenceItem] = Field(default_factory=list, max_length=50)
    human_review: HumanReview = Field(default_factory=HumanReview)
    versions: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_veto(self) -> "RiskDecision":
        if self.hard_veto and not self.veto_reasons:
            raise ValueError("hard_veto=true 时必须提供 veto_reasons")
        if not self.hard_veto and self.veto_reasons:
            raise ValueError("hard_veto=false 时不能提供 veto_reasons")
        if self.hard_veto and self.decision is not RiskDecisionLabel.STAGE_AVOID:
            raise ValueError("硬否决必须输出 stage_avoid")
        if self.hard_veto and self.risk_exposure_band is not RiskExposureBand.HIGH:
            raise ValueError("硬否决的风险暴露等级必须为 high")
        return self


def evidence_ids(items: list[EvidenceItem]) -> list[UUID]:
    return [item.evidence_id for item in items]


__all__ = [
    "HumanReview",
    "HumanReviewStatus",
    "RiskDecision",
    "RiskDecisionLabel",
    "RiskExposureBand",
    "TechnicalRiskInput",
    "TechnicalRiskOutput",
    "evidence_ids",
]
