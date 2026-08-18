"""Environment-selectable financial market data providers."""

from packages.financial_data.akshare_provider import AkShareProvider
from packages.financial_data.provider import MarketDataProvider


def create_market_data_provider(provider: str) -> MarketDataProvider | None:
    """Return ``None`` for deterministic Mock nodes or a real provider adapter."""

    selected = provider.strip().lower()
    if selected == "mock":
        return None
    if selected == "akshare":
        return AkShareProvider()
    raise ValueError(f"不支持的 MARKET_DATA_PROVIDER: {selected}")
