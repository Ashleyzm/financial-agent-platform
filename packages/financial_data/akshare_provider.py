"""AkShare implementation of the normalized market data provider."""

from datetime import UTC, date, datetime
from types import ModuleType
from typing import Any

import akshare as ak
import pandas as pd

from packages.contracts import Market
from packages.financial_data.models import DailyBar, MarketHistory
from packages.financial_data.provider import FinancialDataError


class AkShareProvider:
    name = "akshare"

    def __init__(self, client: ModuleType | Any = ak) -> None:
        self._client = client

    def get_daily_history(
        self,
        symbol: str,
        market: Market,
        *,
        start_date: date,
        end_date: date,
    ) -> MarketHistory:
        normalized_symbol = symbol.strip().upper()
        if start_date > end_date:
            raise FinancialDataError("开始日期不能晚于结束日期")
        try:
            frame = self._fetch(normalized_symbol, market, start_date, end_date)
            bars = self._normalize(frame, start_date, end_date)
        except FinancialDataError:
            raise
        except Exception as exc:
            raise FinancialDataError(f"AkShare 获取 {normalized_symbol} 行情失败: {exc}") from exc
        if len(bars) < 2:
            raise FinancialDataError(
                f"AkShare 未返回足够的 {normalized_symbol} 日线数据，请检查股票代码或日期范围"
            )
        return MarketHistory(
            symbol=normalized_symbol,
            market=market,
            currency={Market.CN: "CNY", Market.HK: "HKD", Market.US: "USD"}[market],
            provider=self.name,
            adjusted=False,
            fetched_at=datetime.now(UTC),
            bars=bars,
        )

    def _fetch(self, symbol: str, market: Market, start_date: date, end_date: date) -> pd.DataFrame:
        start = start_date.strftime("%Y%m%d")
        end = end_date.strftime("%Y%m%d")
        if market is Market.CN:
            return self._client.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start,
                end_date=end,
                adjust="",
            )
        if market is Market.HK:
            return self._client.stock_hk_hist(
                symbol=symbol.zfill(5),
                period="daily",
                start_date=start,
                end_date=end,
                adjust="",
            )
        frame = self._client.stock_us_daily(symbol=symbol, adjust="")
        return frame

    @staticmethod
    def _normalize(frame: pd.DataFrame, start_date: date, end_date: date) -> list[DailyBar]:
        if frame is None or frame.empty:
            return []
        columns = {
            "date": "date" if "date" in frame.columns else "日期",
            "open": "open" if "open" in frame.columns else "开盘",
            "high": "high" if "high" in frame.columns else "最高",
            "low": "low" if "low" in frame.columns else "最低",
            "close": "close" if "close" in frame.columns else "收盘",
            "volume": "volume" if "volume" in frame.columns else "成交量",
        }
        missing = [source for source in columns.values() if source not in frame.columns]
        if missing:
            raise FinancialDataError(f"AkShare 返回字段不完整: {', '.join(missing)}")

        normalized = frame.rename(columns={source: target for target, source in columns.items()})
        normalized = normalized[["date", "open", "high", "low", "close", "volume"]].copy()
        normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce").dt.date
        for column in ["open", "high", "low", "close", "volume"]:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
        normalized = normalized.dropna().sort_values("date")
        normalized = normalized[
            (normalized["date"] >= start_date) & (normalized["date"] <= end_date)
        ]
        return [
            DailyBar(
                trading_date=row.date,
                open=float(row.open),
                high=float(row.high),
                low=float(row.low),
                close=float(row.close),
                volume=float(row.volume),
            )
            for row in normalized.itertuples(index=False)
        ]
