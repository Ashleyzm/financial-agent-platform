"""JSON-compatible serialization for the shared AgentState object."""

from datetime import datetime
from typing import Any
from uuid import UUID

from packages.agent_runtime.state import AgentState
from packages.contracts import (
    AgentName,
    AgentStep,
    ErrorDetail,
    EvidenceItem,
    ForecastReport,
    ForecastRequest,
    MarketSnapshot,
    PredictionResult,
    RiskAssessment,
    TaskStatus,
)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value is not None else None


def _uuid(value: str | None) -> UUID | None:
    return UUID(value) if value is not None else None


def state_to_dict(state: AgentState) -> dict[str, Any]:
    """Convert an AgentState into a stable JSONB payload."""

    return {
        "task_id": str(state["task_id"]),
        "trace_id": str(state["trace_id"]),
        "request": state["request"].model_dump(mode="json"),
        "status": state["status"].value,
        "current_agent": state["current_agent"].value if state["current_agent"] else None,
        "timeline": [step.model_dump(mode="json") for step in state["timeline"]],
        "market_snapshot": (
            state["market_snapshot"].model_dump(mode="json")
            if state["market_snapshot"] is not None
            else None
        ),
        "research_summary": state["research_summary"],
        "evidence": [item.model_dump(mode="json") for item in state["evidence"]],
        "prediction": (
            state["prediction"].model_dump(mode="json") if state["prediction"] is not None else None
        ),
        "risk": state["risk"].model_dump(mode="json") if state["risk"] is not None else None,
        "report": (
            state["report"].model_dump(mode="json") if state["report"] is not None else None
        ),
        "errors": [error.model_dump(mode="json") for error in state["errors"]],
        "created_at": _iso(state["created_at"]),
        "updated_at": _iso(state["updated_at"]),
    }


def state_from_dict(payload: dict[str, Any]) -> AgentState:
    """Reconstruct an AgentState from a JSONB payload."""

    return AgentState(
        task_id=UUID(payload["task_id"]),
        trace_id=UUID(payload["trace_id"]),
        request=ForecastRequest.model_validate(payload["request"]),
        status=TaskStatus(payload["status"]),
        current_agent=(
            AgentName(payload["current_agent"]) if payload.get("current_agent") else None
        ),
        timeline=[AgentStep.model_validate(step) for step in payload["timeline"]],
        market_snapshot=(
            MarketSnapshot.model_validate(payload["market_snapshot"])
            if payload.get("market_snapshot") is not None
            else None
        ),
        research_summary=payload.get("research_summary"),
        evidence=[EvidenceItem.model_validate(item) for item in payload.get("evidence", [])],
        prediction=(
            PredictionResult.model_validate(payload["prediction"])
            if payload.get("prediction") is not None
            else None
        ),
        risk=(
            RiskAssessment.model_validate(payload["risk"])
            if payload.get("risk") is not None
            else None
        ),
        report=(
            ForecastReport.model_validate(payload["report"])
            if payload.get("report") is not None
            else None
        ),
        errors=[ErrorDetail.model_validate(error) for error in payload.get("errors", [])],
        created_at=datetime.fromisoformat(payload["created_at"]),
        updated_at=datetime.fromisoformat(payload["updated_at"]),
    )
