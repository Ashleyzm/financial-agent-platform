"""LangGraph-ready shared state for the financial research workflow."""

from datetime import datetime
from typing import TypedDict
from uuid import UUID, uuid4

from packages.contracts import (
    AgentName,
    AgentStep,
    ErrorDetail,
    EvidenceItem,
    ForecastReport,
    ForecastRequest,
    MarketSnapshot,
    ModelUsage,
    PredictionResult,
    RiskAssessment,
    TaskStatus,
    module_code_for_agent,
    utc_now,
)


class AgentState(TypedDict):
    """Single state object passed between workflow nodes."""

    task_id: UUID
    trace_id: UUID
    request: ForecastRequest
    status: TaskStatus
    current_agent: AgentName | None
    timeline: list[AgentStep]
    market_snapshot: MarketSnapshot | None
    research_summary: str | None
    evidence: list[EvidenceItem]
    prediction: PredictionResult | None
    risk: RiskAssessment | None
    report: ForecastReport | None
    errors: list[ErrorDetail]
    model_usage: ModelUsage
    created_at: datetime
    updated_at: datetime


def create_initial_state(
    request: ForecastRequest,
    *,
    task_id: UUID | None = None,
    trace_id: UUID | None = None,
) -> AgentState:
    """Create a complete, serializable state without shared mutable defaults."""

    now = utc_now()
    return AgentState(
        task_id=task_id or uuid4(),
        trace_id=trace_id or uuid4(),
        request=request,
        status=TaskStatus.QUEUED,
        current_agent=None,
        timeline=[
            AgentStep(agent=agent, module_code=module_code_for_agent(agent)) for agent in AgentName
        ],
        market_snapshot=None,
        research_summary=None,
        evidence=[],
        prediction=None,
        risk=None,
        report=None,
        errors=[],
        model_usage=ModelUsage(),
        created_at=now,
        updated_at=now,
    )
