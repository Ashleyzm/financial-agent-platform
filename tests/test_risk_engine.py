from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from packages.agent_runtime import RiskFusionEngine, TechnicalRiskAgent
from packages.contracts import (
    EvidenceItem,
    EvidenceType,
    HumanReviewStatus,
    RiskDecisionLabel,
    RiskExposureBand,
    TechnicalRiskInput,
)

AS_OF = datetime(2026, 8, 22, tzinfo=UTC)


def make_input(**overrides) -> TechnicalRiskInput:
    values = {
        "symbol": "NVDA",
        "as_of": AS_OF,
        "trend_risk": 20,
        "drawdown_risk": 30,
        "volatility_risk": 40,
        "liquidity_risk": 10,
        "data_quality_risk": 5,
        "provider_version": "snapshot-v1",
    }
    values.update(overrides)
    return TechnicalRiskInput(**values)


def test_technical_agent_is_deterministic_and_traceable() -> None:
    evidence = EvidenceItem(
        evidence_type=EvidenceType.MARKET,
        title="NVDA daily snapshot",
        source="test-provider",
        excerpt="Fixed daily snapshot for W1 acceptance.",
        relevance=1.0,
    )
    output = TechnicalRiskAgent().analyze(make_input(evidence=[evidence]))

    assert output.module_code == "AGT-03"
    assert output.technical_score == 25.0
    assert output.exposure_band is RiskExposureBand.LOW
    assert output.evidence[0].evidence_id == evidence.evidence_id
    assert output.human_review.status is HumanReviewStatus.NOT_REQUIRED
    assert output.versions["technical_rule"] == "technical-risk-v0.1"


def test_technical_agent_degrades_low_quality_data_to_review() -> None:
    output = TechnicalRiskAgent().analyze(make_input(data_quality_risk=80))

    assert output.human_review.required is True
    assert output.human_review.status is HumanReviewStatus.PENDING
    assert "降级" in output.rationale


def test_fusion_hard_veto_is_evaluated_before_average() -> None:
    decision = RiskFusionEngine().fuse(
        as_of=AS_OF,
        technical_score=20,
        event_score=90,
        industry_score=20,
    )

    assert decision.decision is RiskDecisionLabel.STAGE_AVOID
    assert decision.hard_veto is True
    assert decision.aggregate_score < 60
    assert decision.risk_exposure_band is RiskExposureBand.HIGH
    assert decision.human_review.status is HumanReviewStatus.PENDING
    assert len(decision.veto_reasons) == 1


def test_fusion_renormalizes_when_only_technical_factor_exists() -> None:
    decision = RiskFusionEngine().fuse(as_of=AS_OF, technical_score=65)

    assert decision.aggregate_score == 65
    assert decision.decision is RiskDecisionLabel.CAUTIOUS_WATCH
    assert decision.risk_exposure_band is RiskExposureBand.MEDIUM


def test_fusion_marks_large_factor_conflicts_for_review() -> None:
    decision = RiskFusionEngine().fuse(
        as_of=AS_OF,
        technical_score=10,
        event_score=55,
        industry_score=70,
    )

    assert decision.conflicts
    assert decision.human_review.required is True
    assert "分歧" in decision.rationale


def test_risk_contract_rejects_out_of_range_scores() -> None:
    with pytest.raises(ValidationError):
        make_input(trend_risk=101)


def test_human_review_contract_rejects_inconsistent_status() -> None:
    from packages.contracts import HumanReview

    with pytest.raises(ValidationError):
        HumanReview(required=True, status=HumanReviewStatus.NOT_REQUIRED)
