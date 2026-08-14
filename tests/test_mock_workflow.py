from packages.agent_runtime import create_initial_state, run_mock_workflow
from packages.contracts import AgentStatus, ForecastRequest, Market, TaskStatus


def test_mock_workflow_completes_full_agent_chain() -> None:
    state = create_initial_state(ForecastRequest(symbol="NVDA"))

    result = run_mock_workflow(state)

    assert result["status"] is TaskStatus.SUCCEEDED
    assert result["current_agent"] is None
    assert all(step.status is AgentStatus.SUCCEEDED for step in result["timeline"])
    assert result["market_snapshot"] is not None
    assert result["prediction"] is not None
    assert result["risk"] is not None
    assert result["report"] is not None
    assert result["report"].prediction.model_name == "mock-rule-model-v0.1"
    assert result["evidence"][0].metadata["mock"] is True


def test_mock_workflow_uses_hkd_for_hong_kong_market() -> None:
    state = create_initial_state(ForecastRequest(symbol="0700", market=Market.HK))

    result = run_mock_workflow(state)

    assert result["market_snapshot"] is not None
    assert result["market_snapshot"].currency == "HKD"
