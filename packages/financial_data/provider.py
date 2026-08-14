"""Provider interface shared by Data Agent implementations."""

from datetime import date
from typing import Protocol

from packages.contracts import Market
from packages.financial_data.models import MarketHistory


class FinancialDataError(RuntimeError):
    """A safe, user-readable error raised by an external financial data source."""


class MarketDataProvider(Protocol):
    name: str

    def get_daily_history(
        self,
        symbol: str,
        market: Market,
        *,
        start_date: date,
        end_date: date,
    ) -> MarketHistory: ...
