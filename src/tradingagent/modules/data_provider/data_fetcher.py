"""
Data fetcher that proxies market data requests through broker abstractions.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import yfinance as yf
from config import config

from ...core.brokers import BrokerFactory
from ...core.interfaces import IBroker


class DataFetcher:
    """
    Market data fetcher that delegates to concrete broker implementations.
    """

    def __init__(
        self,
        broker: Optional[IBroker] = None,
        *,
        provider: Optional[str] = None,
        broker_id: Optional[str] = None,
        **broker_overrides: Any,
    ) -> None:
        """
        Initialize data fetcher.

        Args:
            broker: Pre-configured broker instance implementing IBroker.
            provider: Backwards-compatible alias for broker_id.
            broker_id: Broker identifier registered with BrokerFactory/config.
            **broker_overrides: Extra keyword arguments forwarded to broker resolution.
        """
        requested_id = broker_id or provider
        if isinstance(requested_id, str):
            requested_id = requested_id.lower()
        self._requested_broker_id = requested_id

        self._broker_overrides = dict(broker_overrides)

        self._broker: Optional[IBroker] = broker
        if self._broker is not None and not self._broker.is_connected():
            self._broker.connect()

        # Cache placeholders (reserved for future enhancements)
        self.cache: Dict[str, pd.DataFrame] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        self.cache_expiry = timedelta(minutes=15)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def fetch_stock_data(
        self,
        symbol: str,
        start_date: Union[str, datetime] = None,
        end_date: Union[str, datetime] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Fetch stock data for a given symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval ('1d', '1h', '5m', etc.)

        Returns:
            DataFrame with OHLCV data.
        """
        broker = self._ensure_broker()
        bars = broker.get_historical_bars(
            symbol=symbol,
            start=start_date,
            end=end_date,
            interval=interval,
        )
        return self._bars_to_dataframe(symbol, bars)

    def fetch_multiple_stocks(
        self,
        symbols: List[str],
        start_date: Union[str, datetime] = None,
        end_date: Union[str, datetime] = None,
        interval: str = "1d",
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple stocks.

        Args:
            symbols: List of stock symbols
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval

        Returns:
            Dictionary mapping symbols to DataFrames
        """
        results: Dict[str, pd.DataFrame] = {}
        for symbol in symbols:
            try:
                results[symbol] = self.fetch_stock_data(
                    symbol, start_date, end_date, interval
                )
                time.sleep(0.1)  # Basic rate limiting
            except Exception as exc:  # pragma: no cover - defensive logging
                print(f"Error fetching data for {symbol}: {exc}")
                results[symbol] = pd.DataFrame()
        return results

    def get_current_price(self, symbol: str) -> float:
        """
        Get current price for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Current price
        """
        broker = self._ensure_broker()
        price = broker.get_current_price(symbol)
        if price is not None:
            return float(price)

        # Fallback: use the most recent close price
        data = self.fetch_stock_data(
            symbol, start_date=datetime.now() - timedelta(days=5)
        )
        return data["close"].iloc[-1] if not data.empty else 0.0

    def get_stock_info(self, symbol: str) -> Dict[str, Union[str, float]]:
        """
        Retrieve high-level stock information.
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                "symbol": symbol,
                "name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "dividend_yield": info.get("dividendYield", 0),
                "beta": info.get("beta", 0),
                "52w_high": info.get("fiftyTwoWeekHigh", 0),
                "52w_low": info.get("fiftyTwoWeekLow", 0),
            }
        except Exception as exc:  # pragma: no cover - defensive
            print(f"Error getting stock info for {symbol}: {exc}")
            return {}

    def clear_cache(self) -> None:
        """Clear any cached data."""
        self.cache.clear()
        self.cache_timestamps.clear()

    def get_cache_stats(self) -> Dict[str, Union[int, float]]:
        """
        Return cache statistics.
        """
        return {
            "entries": len(self.cache),
            "expiry_minutes": self.cache_expiry.total_seconds() / 60.0,
        }

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _ensure_broker(self) -> IBroker:
        """
        Lazily create and connect a broker for the requested provider.
        """
        if self._broker is not None:
            if not self._broker.is_connected():
                self._broker.connect()
            return self._broker

        broker_type, params = config.resolve_broker(
            self._requested_broker_id,
            **self._broker_overrides,
        )
        broker = BrokerFactory.create(broker_type, **params)
        broker.connect()
        self._broker = broker
        return broker

    @staticmethod
    def _bars_to_dataframe(symbol: str, bars: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert broker bar data into a normalised DataFrame.
        """
        expected_columns = ["open", "high", "low", "close", "volume"]
        if not bars:
            # Return a normalized empty frame so callers can handle the absence of data
            # without relying on exceptions.
            return pd.DataFrame(columns=expected_columns)

        df = pd.DataFrame(bars)
        if df.empty:
            return pd.DataFrame(columns=expected_columns)

        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
            df = df.dropna(subset=["timestamp"])
            df = df.set_index("timestamp")
            df.index = df.index.tz_convert("UTC").tz_localize(None)
        else:
            df.index = pd.to_datetime(df.index, utc=True, errors="coerce")
            df = df.dropna()
            df.index = df.index.tz_convert("UTC").tz_localize(None)
            df.index.name = "date"

        df.columns = [str(col).lower() for col in df.columns]
        df = df.sort_index()

        for column in expected_columns:
            if column not in df.columns:
                df[column] = pd.NA

        df = df[expected_columns]
        for column in expected_columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

        return df


__all__ = ["DataFetcher"]
