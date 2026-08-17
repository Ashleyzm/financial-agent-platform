"""Deterministic mock workflow used before LangGraph and real providers are connected."""

from collections.abc import Callable
from time import perf_counter

from packages.agent_runtime.state import AgentState
from packages.contracts import (
    AgentName,
    AgentStatus,
    ConfidenceLevel,
    ErrorDetail,
    EvidenceItem,
    EvidenceType,
    ForecastDirection,
    ForecastReport,
    MarketSnapshot,
    PredictionResult,
    RiskAssessment,
    RiskLevel,
    TaskStatus,
    utc_now,
)


class WorkflowExecutionError(RuntimeError):
    """Raised when the mock workflow cannot complete."""


Node = Callable[[AgentState], None]


def _supervisor_node(state: AgentState) -> None:
    state["research_summary"] = "任务已拆分为行情、研究、预测、风险和报告五个步骤。"


def _data_node(state: AgentState) -> None:
    symbol = state["request"].symbol
    seed = sum(ord(character) for character in symbol)
    price_change = round(((seed % 21) - 10) / 100, 4)
    currency = {"CN": "CNY", "HK": "HKD", "US": "USD"}[state["request"].market.value]
    state["market_snapshot"] = MarketSnapshot(
        symbol=symbol,
        price=round(80 + (seed % 320) + 0.25, 2),
        currency=currency,
        as_of=utc_now(),
        price_change_30d=price_change,
        volatility_30d=round(0.2 + (seed % 15) / 100, 4),
        volume=float(1_000_000 + seed * 100),
    )


def _research_node(state: AgentState) -> None:
    symbol = state["request"].symbol
    state["evidence"].append(
        EvidenceItem(
            evidence_type=EvidenceType.RESEARCH,
            title=f"{symbol} Mock 研究摘要",
            source="mock-research-provider",
            excerpt="该证据为流程演示数据，后续由真实新闻、财报和研报 Provider 替换。",
            relevance=0.8,
            metadata={"mock": True},
        )
    )
    state["research_summary"] = (
        f"{symbol} 当前使用 Mock 数据完成研究流程验证，尚未接入真实新闻与财务数据。"
    )


def _prediction_node(state: AgentState) -> None:
    snapshot = state["market_snapshot"]
    if snapshot is None:
        raise WorkflowExecutionError("Prediction Agent 缺少市场快照")
    change = snapshot.price_change_30d or 0
    probability = min(0.7, max(0.3, round(0.5 + change, 4)))
    if probability >= 0.58:
        direction = ForecastDirection.BULLISH
    elif probability <= 0.42:
        direction = ForecastDirection.BEARISH
    else:
        direction = ForecastDirection.NEUTRAL
    state["prediction"] = PredictionResult(
        horizon_days=state["request"].horizon_days,
        direction=direction,
        upward_probability=probability,
        expected_return=round((probability - 0.5) / 2, 4),
        model_name="mock-rule-model-v0.1",
    )


def _risk_node(state: AgentState) -> None:
    snapshot = state["market_snapshot"]
    if snapshot is None:
        raise WorkflowExecutionError("Risk Agent 缺少市场快照")
    volatility = snapshot.volatility_30d or 0
    if volatility >= 0.32:
        level = RiskLevel.HIGH
    elif volatility >= 0.24:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.LOW
    market_evidence = next(
        (item for item in state["evidence"] if item.evidence_type is EvidenceType.MARKET), None
    )
    market_factor = (
        f"行情来源为 {market_evidence.source} 公开数据"
        if market_evidence is not None
        else "当前使用 Mock 行情"
    )
    state["risk"] = RiskAssessment(
        level=level,
        confidence=ConfidenceLevel.LOW,
        volatility=volatility,
        max_drawdown=round(-volatility / 2, 4),
        factors=[market_factor, "尚未接入宏观与实时新闻数据"],
    )


def _report_node(state: AgentState) -> None:
    prediction = state["prediction"]
    risk = state["risk"]
    summary = state["research_summary"]
    if prediction is None or risk is None or summary is None:
        raise WorkflowExecutionError("Report Agent 缺少上游结果")
    request = state["request"]
    state["report"] = ForecastReport(
        symbol=request.symbol,
        market=request.market,
        prediction=prediction,
        research_summary=summary,
        evidence=state["evidence"],
        risk=risk,
    )


WORKFLOW: tuple[tuple[AgentName, Node], ...] = (
    (AgentName.SUPERVISOR, _supervisor_node),
    (AgentName.DATA, _data_node),
    (AgentName.RESEARCH, _research_node),
    (AgentName.PREDICTION, _prediction_node),
    (AgentName.RISK, _risk_node),
    (AgentName.REPORT, _report_node),
)


def _update_step(
    state: AgentState,
    agent: AgentName,
    *,
    status: AgentStatus,
    started_at=None,
    finished_at=None,
    duration_ms: int | None = None,
    summary: str | None = None,
    error: ErrorDetail | None = None,
) -> None:
    for index, step in enumerate(state["timeline"]):
        if step.agent is agent:
            state["timeline"][index] = step.model_copy(
                update={
                    "status": status,
                    "started_at": started_at if started_at is not None else step.started_at,
                    "finished_at": finished_at,
                    "duration_ms": duration_ms,
                    "summary": summary,
                    "error": error,
                }
            )
            return
    raise WorkflowExecutionError(f"找不到 Agent 时间线节点: {agent}")


def run_mock_workflow(state: AgentState) -> AgentState:
    """Run all mock nodes synchronously and return the updated state."""

    if state["status"] not in {TaskStatus.QUEUED, TaskStatus.RUNNING}:
        raise WorkflowExecutionError(f"任务状态 {state['status']} 不允许执行")

    for agent, _ in WORKFLOW:
        state = run_mock_node(state, agent)
        if state["status"] is TaskStatus.FAILED:
            break
    return state


def run_mock_node(
    state: AgentState, agent: AgentName, *, node_override: Node | None = None
) -> AgentState:
    """Run one business node so LangGraph can checkpoint every agent boundary."""

    if state["status"] is TaskStatus.FAILED:
        return state
    if state["status"] not in {TaskStatus.QUEUED, TaskStatus.RUNNING}:
        raise WorkflowExecutionError(f"任务状态 {state['status']} 不允许执行")

    nodes = dict(WORKFLOW)
    node = node_override or nodes[agent]
    started_at = utc_now()
    started_clock = perf_counter()
    state["status"] = TaskStatus.RUNNING
    state["current_agent"] = agent
    state["updated_at"] = started_at
    _update_step(state, agent, status=AgentStatus.RUNNING, started_at=started_at)
    try:
        node(state)
    except Exception as exc:
        finished_at = utc_now()
        error = ErrorDetail(
            code=getattr(exc, "code", "agent_execution_failed"),
            message=str(exc),
            agent=agent,
            retryable=bool(getattr(exc, "retryable", False)),
        )
        state["errors"].append(error)
        state["status"] = TaskStatus.FAILED
        state["current_agent"] = None
        state["updated_at"] = finished_at
        _update_step(
            state,
            agent,
            status=AgentStatus.FAILED,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=max(0, round((perf_counter() - started_clock) * 1000)),
            error=error,
        )
        return state

    finished_at = utc_now()
    _update_step(
        state,
        agent,
        status=AgentStatus.SUCCEEDED,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=max(0, round((perf_counter() - started_clock) * 1000)),
        summary=f"{agent.value} 节点执行完成",
    )
    state["updated_at"] = finished_at
    if agent is AgentName.REPORT:
        state["status"] = TaskStatus.SUCCEEDED
        state["current_agent"] = None
    return state
