"""Normalized financial data returned by every provider."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from packages.contracts import Market


class FinancialDataModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DailyBar(FinancialDataModel):
    trading_date: date
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)


class MarketHistory(FinancialDataModel):
    symbol: str
    market: Market
    currency: str = Field(min_length=3, max_length=3)
    provider: str
    adjusted: bool = False
    fetched_at: datetime
    bars: list[DailyBar] = Field(min_length=2)
