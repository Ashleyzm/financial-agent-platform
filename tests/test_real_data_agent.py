from datetime import UTC, date, datetime, timedelta

from langgraph.checkpoint.memory import InMemorySaver

from packages.agent_runtime import LangGraphWorkflowRunner, create_initial_state
from packages.contracts import AgentName, ForecastRequest, Market, TaskStatus
from packages.financial_data import DailyBar, FinancialDataError, MarketHistory


class StaticProvider:
    name = "test-provider"

    def get_daily_history(self, symbol, market, *, start_date, end_date):
        bars = [
            DailyBar(
                trading_date=date(2026, 7, 1) + timedelta(days=index),
                open=100 + index,
                high=102 + index,
                low=99 + index,
                close=101 + index,
                volume=1_000_000 + index,
            )
            for index in range(35)
        ]
        return MarketHistory(
            symbol=symbol,
            market=market,
            currency="USD",
            provider=self.name,
            fetched_at=datetime.now(UTC),
            bars=bars,
        )


class FailingProvider:
    name = "failing-provider"

    def get_daily_history(self, symbol, market, *, start_date, end_date):
        raise FinancialDataError("测试数据源不可用")


def test_langgraph_data_agent_uses_real_provider() -> None:
    runner = LangGraphWorkflowRunner(InMemorySaver(), market_data_provider=StaticProvider())
    state = create_initial_state(ForecastRequest(symbol="NVDA", market=Market.US))

    result = runner(state)

    assert result["status"] is TaskStatus.SUCCEEDED
    assert result["market_snapshot"].price == 135
    assert result["market_snapshot"].price_change_30d > 0
    assert result["evidence"][0].source == "test-provider"
    assert result["evidence"][0].metadata["mock"] is False
    assert len(result["evidence"]) == 2


def test_data_source_failure_stops_graph_with_traceable_error() -> None:
    runner = LangGraphWorkflowRunner(InMemorySaver(), market_data_provider=FailingProvider())
    state = create_initial_state(ForecastRequest(symbol="NVDA"))

    result = runner(state)

    assert result["status"] is TaskStatus.FAILED
    assert result["errors"][-1].agent is AgentName.DATA
    assert result["errors"][-1].message == "测试数据源不可用"
    assert result["report"] is None
