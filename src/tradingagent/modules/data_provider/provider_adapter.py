"""
SimpleMarketDataProvider - IDataProvider adapter backed by DataFetcher.

属于 TradingAgent 层（底层数据操作）。
提供统一的数据接口供上层组件（如 SimulationBroker）注入使用。
"""

from typing import Optional, Dict, List
from datetime import datetime, timedelta

from ...core.interfaces.data_provider import IDataProvider
from .data_fetcher import DataFetcher


class SimpleMarketDataProvider(IDataProvider):
    """基于 DataFetcher 的简单数据提供器适配器。"""

    def __init__(self, provider: Optional[str] = None) -> None:
        self._fetcher = DataFetcher(provider=provider)

    def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ):
        return self._fetcher.fetch_stock_data(symbol, start_date, end_date, interval)

    def get_current_price(self, symbol: str) -> Optional[float]:
        try:
            price = float(self._fetcher.get_current_price(symbol))
            return price if price > 0 else None
        except Exception:
            return None

    def get_batch_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        results: Dict[str, float] = {}
        for sym in symbols:
            p = self.get_current_price(sym)
            if p is not None:
                results[sym] = p
        return results
