#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DataProvider and RealTimeDataProvider implementations.

This module exposes a facade for fetching market data (DataProvider) as well
as a simple in-memory realtime provider (RealTimeDataProvider). It composes the
lower-level `DataFetcher` for external data access and `DataManager` for local
storage/caching concerns.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

from .data_manager import DataManager
from .data_fetcher import DataFetcher

logger = logging.getLogger(__name__)


class DataProvider:
    """
    Unified data access facade that combines fetching remote market data and
    optional local persistence/caching.
    """

    def __init__(self, provider: str = None):
        """
        Initialize the provider facade.

        Args:
            provider: Identifier of the upstream data source (e.g. "yfinance").
        """
        self._fetcher = DataFetcher(provider=provider)
        self._manager = DataManager()
        logger.info("DataProvider initialized")

    def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLCV data from the upstream provider.

        Args:
            symbol: Ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval (e.g. 1d, 1h, 5m)
        """
        return self._fetcher.fetch_stock_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
        )

    def get_latest_data(
        self,
        symbol: str,
        days: int = 60,
        interval: str = "1d",
    ) -> Optional[pd.DataFrame]:
        """
        Convenience helper to fetch the most recent N days of data.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        return self.get_historical_data(
            symbol=symbol,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            interval=interval,
        )

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Retrieve the latest available market price for a symbol.
        """
        return self._fetcher.get_current_price(symbol)

    def get_batch_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Retrieve latest prices for a collection of symbols.
        """
        prices: Dict[str, float] = {}
        for symbol in symbols:
            price = self.get_current_price(symbol)
            if price:
                prices[symbol] = price

        logger.info("Fetched prices for %s/%s symbols", len(prices), len(symbols))
        return prices

    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch metadata for a symbol (sector, market cap, etc).
        """
        return self._fetcher.get_stock_info(symbol)

    def clear_cache(self) -> None:
        """
        Clear any in-memory fetcher caches.
        """
        self._fetcher.clear_cache()
        logger.info("Cleared data fetcher cache")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Return statistics about the fetcher's cache usage.
        """
        return self._fetcher.get_cache_stats()


class RealTimeDataProvider(DataProvider):
    """
    Simple realtime-oriented provider that tracks subscribed symbols and
    exposes convenience helpers around batch price retrieval.
    """

    def __init__(self, poll_interval: int = 1):
        super().__init__()
        self.poll_interval = poll_interval
        self.subscribed_symbols: set[str] = set()
        logger.info(
            "RealTimeDataProvider initialized (poll interval: %s sec)", poll_interval
        )

    def subscribe(self, symbols: List[str]) -> None:
        self.subscribed_symbols.update(symbols)
        logger.info("Subscribed realtime symbols: %s", symbols)

    def unsubscribe(self, symbols: List[str]) -> None:
        self.subscribed_symbols.difference_update(symbols)
        logger.info("Unsubscribed realtime symbols: %s", symbols)

    def get_subscribed_prices(self) -> Dict[str, float]:
        return self.get_batch_current_prices(list(self.subscribed_symbols))


__all__ = ["DataProvider", "RealTimeDataProvider"]
