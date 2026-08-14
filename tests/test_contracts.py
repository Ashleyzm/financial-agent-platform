from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from packages.contracts import (
    ConfidenceLevel,
    EvidenceItem,
    EvidenceType,
    ForecastDirection,
    ForecastReport,
    ForecastRequest,
    Market,
    PredictionResult,
    RiskAssessment,
    RiskLevel,
)


def test_forecast_request_normalizes_symbol() -> None:
    request = ForecastRequest(symbol=" nvda ", market=Market.US)

    assert request.symbol == "NVDA"
    assert request.horizon_days == 5


@pytest.mark.parametrize("horizon_days", [0, 31])
def test_forecast_request_rejects_invalid_horizon(horizon_days: int) -> None:
    with pytest.raises(ValidationError):
        ForecastRequest(symbol="NVDA", horizon_days=horizon_days)


def test_contracts_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ForecastRequest(symbol="NVDA", unsupported=True)


def test_forecast_report_round_trips_as_json() -> None:
    now = datetime.now(UTC)
    prediction = PredictionResult(
        horizon_days=5,
        direction=ForecastDirection.BULLISH,
        upward_probability=0.68,
        expected_return=0.035,
        model_name="xgboost-demo",
    )
    risk = RiskAssessment(
        level=RiskLevel.HIGH,
        confidence=ConfidenceLevel.MEDIUM,
        volatility=0.42,
        max_drawdown=-0.18,
        factors=["估值较高", "市场波动"],
    )
    evidence = EvidenceItem(
        evidence_type=EvidenceType.NEWS,
        title="AI demand remains strong",
        source="mock-news",
        url="https://example.com/news/1",
        published_at=now,
        excerpt="A short, traceable evidence excerpt.",
        relevance=0.9,
    )
    report = ForecastReport(
        symbol="NVDA",
        market=Market.US,
        prediction=prediction,
        research_summary="收入趋势和 AI 需求构成主要支持因素。",
        evidence=[evidence],
        risk=risk,
    )

    restored = ForecastReport.model_validate_json(report.model_dump_json())

    assert restored == report
    assert restored.disclaimer.endswith("不构成投资建议。")


def test_prediction_probability_is_bounded() -> None:
    with pytest.raises(ValidationError):
        PredictionResult(
            horizon_days=5,
            direction=ForecastDirection.BULLISH,
            upward_probability=1.01,
            model_name="invalid-demo",
        )
