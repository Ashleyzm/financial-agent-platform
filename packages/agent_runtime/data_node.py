"""Data Agent logic that converts provider history into model-ready features."""

from datetime import UTC, datetime, time, timedelta
from math import sqrt
from statistics import pstdev

from packages.agent_runtime.state import AgentState
from packages.contracts import EvidenceItem, EvidenceType, MarketSnapshot, utc_now
from packages.financial_data import MarketDataProvider


def populate_real_market_data(state: AgentState, provider: MarketDataProvider) -> None:
    """Fetch recent daily bars and populate a traceable market snapshot."""

    end_date = utc_now().date()
    history = provider.get_daily_history(
        state["request"].symbol,
        state["request"].market,
        start_date=end_date - timedelta(days=90),
        end_date=end_date,
    )
    bars = history.bars
    closes = [bar.close for bar in bars]
    baseline_index = max(0, len(closes) - 31)
    price_change_30d = closes[-1] / closes[baseline_index] - 1
    returns = [
        current / previous - 1 for previous, current in zip(closes, closes[1:], strict=False)
    ]
    recent_returns = returns[-30:]
    volatility_30d = pstdev(recent_returns) * sqrt(252) if len(recent_returns) >= 2 else 0.0
    latest = bars[-1]
    state["market_snapshot"] = MarketSnapshot(
        symbol=history.symbol,
        price=latest.close,
        currency=history.currency,
        as_of=datetime.combine(latest.trading_date, time.min, tzinfo=UTC),
        price_change_30d=round(price_change_30d, 6),
        volatility_30d=round(volatility_30d, 6),
        volume=latest.volume,
    )
    state["evidence"].append(
        EvidenceItem(
            evidence_type=EvidenceType.MARKET,
            title=f"{history.symbol} 日线行情",
            source=history.provider,
            published_at=history.fetched_at,
            excerpt=(
                f"截至 {latest.trading_date.isoformat()} 收盘价 {latest.close:.2f} "
                f"{history.currency}，近 30 个交易日区间涨跌 {price_change_30d:.2%}。"
            ),
            relevance=1.0,
            metadata={
                "provider": history.provider,
                "bar_count": len(bars),
                "adjusted": history.adjusted,
                "mock": False,
            },
        )
    )
