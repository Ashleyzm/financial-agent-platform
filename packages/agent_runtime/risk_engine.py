"""Deterministic technical-risk Agent and three-factor fusion rules."""

from collections.abc import Iterable
from datetime import datetime

from packages.contracts import EvidenceItem
from packages.contracts.risk import (
    HumanReview,
    HumanReviewStatus,
    RiskDecision,
    RiskDecisionLabel,
    RiskExposureBand,
    TechnicalRiskInput,
    TechnicalRiskOutput,
)


class TechnicalRiskAgent:
    """Compute a reproducible AGT-03 score from normalized daily inputs."""

    module_code = "AGT-03"
    weights = {
        "trend_risk": 0.30,
        "drawdown_risk": 0.25,
        "volatility_risk": 0.25,
        "liquidity_risk": 0.10,
        "data_quality_risk": 0.10,
    }

    def analyze(self, inputs: TechnicalRiskInput) -> TechnicalRiskOutput:
        factors = {name: round(getattr(inputs, name), 4) for name in self.weights}
        score = round(sum(factors[name] * weight for name, weight in self.weights.items()), 2)
        band = _band(score)
        invalidators = [
            "行情快照过期或 Provider 版本变化时需重新计算",
            "出现日内重大事件时，技术结论不能单独作为最终判断",
        ]
        review_required = score >= 66 or inputs.data_quality_risk >= 50
        review = HumanReview(
            required=review_required,
            status=HumanReviewStatus.PENDING if review_required else HumanReviewStatus.NOT_REQUIRED,
        )
        rationale = (
            f"{inputs.symbol} 技术风险得分 {score:.2f}/100，"
            f"趋势 {factors['trend_risk']:.1f}、回撤 {factors['drawdown_risk']:.1f}、"
            f"波动 {factors['volatility_risk']:.1f}、流动性 {factors['liquidity_risk']:.1f}、"
            f"数据质量 {factors['data_quality_risk']:.1f}。"
        )
        if inputs.data_quality_risk >= 50:
            rationale += " 数据质量风险较高，结论已降级并要求人工复核。"
        return TechnicalRiskOutput(
            symbol=inputs.symbol,
            as_of=inputs.as_of,
            technical_score=score,
            exposure_band=band,
            factor_scores=factors,
            rationale=rationale,
            invalidators=invalidators,
            evidence=inputs.evidence,
            human_review=review,
            versions={"technical_rule": "technical-risk-v0.1", "provider": inputs.provider_version},
        )


class RiskFusionEngine:
    """Apply priority and hard-veto rules to available factor scores."""

    module_code = "AGT-06"
    weights = {"technical": 0.45, "event": 0.30, "industry": 0.25}
    hard_veto_thresholds = {"technical": 90.0, "event": 80.0, "industry": 80.0}
    conflict_gap = 40.0

    def fuse(
        self,
        *,
        as_of: datetime,
        technical_score: float | None = None,
        event_score: float | None = None,
        industry_score: float | None = None,
        evidence: Iterable[EvidenceItem] = (),
        versions: dict[str, str] | None = None,
    ) -> RiskDecision:
        scores = {"technical": technical_score, "event": event_score, "industry": industry_score}
        available = {name: value for name, value in scores.items() if value is not None}
        if not available:
            raise ValueError("至少需要一个三因子风险得分")
        if any(value < 0 or value > 100 for value in available.values()):
            raise ValueError("风险得分必须位于 0 到 100")

        total_weight = sum(self.weights[name] for name in available)
        aggregate = round(
            sum(value * self.weights[name] for name, value in available.items()) / total_weight,
            2,
        )
        veto_reasons = [
            f"{name} 风险得分 {value:.2f} 达到硬否决阈值 {self.hard_veto_thresholds[name]:.0f}"
            for name, value in available.items()
            if value >= self.hard_veto_thresholds[name]
        ]
        ordered = sorted(available.items(), key=lambda item: item[1])
        conflicts = []
        if len(ordered) >= 2 and ordered[-1][1] - ordered[0][1] >= self.conflict_gap:
            conflicts.append(
                f"{ordered[-1][0]} 与 {ordered[0][0]} 风险得分相差 "
                f"{ordered[-1][1] - ordered[0][1]:.2f}，需要解释冲突"
            )
        hard_veto = bool(veto_reasons)
        if hard_veto:
            decision = RiskDecisionLabel.STAGE_AVOID
        elif aggregate >= 60:
            decision = RiskDecisionLabel.CAUTIOUS_WATCH
        else:
            decision = RiskDecisionLabel.NORMAL_RESEARCH
        review_required = hard_veto or bool(conflicts) or aggregate >= 60
        review = HumanReview(
            required=review_required,
            status=HumanReviewStatus.PENDING if review_required else HumanReviewStatus.NOT_REQUIRED,
        )
        rationale = f"可用因子 {', '.join(available)}，归一化加权风险得分 {aggregate:.2f}/100。"
        if hard_veto:
            rationale += " 先执行硬否决，不能由其他低风险因子平均抵消。"
        elif conflicts:
            rationale += " 因子之间存在显著分歧，进入人工复核。"
        invalidators = [
            "任一因子更新、证据过期或规则版本变化时必须回放",
            "补齐事件和产业因子后需要重新执行融合，不得沿用单因子结论",
        ]
        evidence_list = list(evidence)
        return RiskDecision(
            decision=decision,
            as_of=as_of,
            technical_score=technical_score,
            event_score=event_score,
            industry_score=industry_score,
            aggregate_score=aggregate,
            risk_exposure_band=RiskExposureBand.HIGH if hard_veto else _band(aggregate),
            hard_veto=hard_veto,
            veto_reasons=veto_reasons,
            conflicts=conflicts,
            rationale=rationale,
            invalidators=invalidators,
            evidence=evidence_list,
            human_review=review,
            versions=versions or {"fusion_rule": "risk-fusion-v0.1"},
            metadata={"module_code": self.module_code, "evidence_count": len(evidence_list)},
        )


def _band(score: float) -> RiskExposureBand:
    if score >= 66:
        return RiskExposureBand.HIGH
    if score >= 34:
        return RiskExposureBand.MEDIUM
    return RiskExposureBand.LOW


__all__ = ["RiskFusionEngine", "TechnicalRiskAgent"]
