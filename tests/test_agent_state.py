from packages.agent_runtime import create_initial_state
from packages.contracts import AgentName, AgentStatus, ForecastRequest, TaskStatus


def test_initial_state_is_complete_and_traceable() -> None:
    state = create_initial_state(ForecastRequest(symbol="NVDA"))

    assert state["status"] is TaskStatus.QUEUED
    assert state["current_agent"] is None
    assert state["task_id"] != state["trace_id"]
    assert [step.agent for step in state["timeline"]] == list(AgentName)
    assert all(step.status is AgentStatus.PENDING for step in state["timeline"])
    assert state["errors"] == []
    assert state["report"] is None


def test_initial_state_does_not_share_mutable_values() -> None:
    first = create_initial_state(ForecastRequest(symbol="NVDA"))
    second = create_initial_state(ForecastRequest(symbol="AAPL"))

    first["evidence"].append("sentinel")  # type: ignore[arg-type]

    assert second["evidence"] == []
