from datetime import UTC, date, datetime
from types import SimpleNamespace

import pandas as pd
import pytest

from packages.contracts import Market
from packages.financial_data import AkShareProvider, FinancialDataError


def test_akshare_normalizes_chinese_a_share_columns() -> None:
    frame = pd.DataFrame(
        {
            "日期": ["2026-08-10", "2026-08-11"],
            "开盘": [10.0, 10.5],
            "最高": [10.8, 11.0],
            "最低": [9.8, 10.2],
            "收盘": [10.6, 10.9],
            "成交量": [1000, 1200],
        }
    )
    client = SimpleNamespace(stock_zh_a_hist=lambda **_: frame)

    result = AkShareProvider(client).get_daily_history(
        "000001",
        Market.CN,
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 12),
    )

    assert result.provider == "akshare"
    assert result.currency == "CNY"
    assert result.bars[-1].close == 10.9
    assert result.bars[-1].trading_date == date(2026, 8, 11)


def test_akshare_filters_us_history_to_requested_dates() -> None:
    frame = pd.DataFrame(
        {
            "date": ["2026-07-31", "2026-08-10", "2026-08-11"],
            "open": [100, 101, 102],
            "high": [102, 103, 104],
            "low": [99, 100, 101],
            "close": [101, 102, 103],
            "volume": [1000, 1100, 1200],
        }
    )
    client = SimpleNamespace(stock_us_daily=lambda **_: frame)

    result = AkShareProvider(client).get_daily_history(
        "nvda",
        Market.US,
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 12),
    )

    assert result.symbol == "NVDA"
    assert result.currency == "USD"
    assert len(result.bars) == 2


def test_akshare_rejects_empty_or_insufficient_history() -> None:
    client = SimpleNamespace(stock_hk_hist=lambda **_: pd.DataFrame())

    with pytest.raises(FinancialDataError, match="未返回足够"):
        AkShareProvider(client).get_daily_history(
            "00700",
            Market.HK,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 12),
        )


def test_market_history_fetch_time_is_timezone_aware() -> None:
    frame = pd.DataFrame(
        {
            "date": ["2026-08-10", "2026-08-11"],
            "open": [100, 101],
            "high": [102, 103],
            "low": [99, 100],
            "close": [101, 102],
            "volume": [1000, 1100],
        }
    )
    result = AkShareProvider(SimpleNamespace(stock_us_daily=lambda **_: frame)).get_daily_history(
        "AAPL",
        Market.US,
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 12),
    )

    assert isinstance(result.fetched_at, datetime)
    assert result.fetched_at.tzinfo is UTC
