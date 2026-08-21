"""Prove that market-data and LLM providers can be replaced by injection."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta

from langgraph.checkpoint.memory import InMemorySaver

from packages.agent_runtime import LangGraphWorkflowRunner, create_initial_state
from packages.contracts import EvidenceType, ForecastRequest, Market, TaskStatus
from packages.financial_data import DailyBar, MarketHistory
from packages.model_provider import MockLLMProvider


class SampleMarketProvider:
    """Small deterministic provider that follows the public market-data protocol."""

    name = "sample-market"

    def get_daily_history(
        self,
        symbol: str,
        market: Market,
        *,
        start_date: date,
        end_date: date,
    ) -> MarketHistory:
        first_date = max(start_date, end_date - timedelta(days=44))
        bars = [
            DailyBar(
                trading_date=first_date + timedelta(days=index),
                open=100 + index,
                high=101 + index,
                low=99 + index,
                close=100.5 + index,
                volume=1_000_000 + index * 1_000,
            )
            for index in range(45)
        ]
        return MarketHistory(
            symbol=symbol,
            market=market,
            currency="USD",
            provider=self.name,
            fetched_at=datetime.now(UTC),
            bars=bars,
        )


class SampleLLMProvider(MockLLMProvider):
    """Mock implementation with a distinct identity for replacement evidence."""

    name = "sample-llm"


def run_demo() -> dict[str, object]:
    runner = LangGraphWorkflowRunner(
        InMemorySaver(),
        market_data_provider=SampleMarketProvider(),
        llm_provider=SampleLLMProvider(),
    )
    result = runner(create_initial_state(ForecastRequest(symbol="NVDA", market=Market.US)))
    market_evidence = next(
        item for item in result["evidence"] if item.evidence_type is EvidenceType.MARKET
    )

    assert result["status"] is TaskStatus.SUCCEEDED
    assert market_evidence.source == "sample-market"
    assert result["model_usage"].provider == "sample-llm"
    assert result["report"] is not None
    return {
        "gate": "F0-08",
        "status": "passed",
        "module_code": "AGT-03",
        "market_provider": market_evidence.source,
        "llm_provider": result["model_usage"].provider,
        "task_status": result["status"].value,
    }


def main() -> None:
    print(json.dumps(run_demo(), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
