"""
Data fetcher for retrieving market data from various sources.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
import requests
import yfinance as yf
from config import config

try:  # Optional dependency for Alpaca market data
    from alpaca.common.exceptions import APIError
    from alpaca.data.enums import Adjustment, DataFeed
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest, StockLatestTradeRequest
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
except ImportError:  # pragma: no cover - dependency may be absent
    APIError = Exception  # type: ignore
    StockHistoricalDataClient = None  # type: ignore
    StockBarsRequest = None  # type: ignore
    StockLatestTradeRequest = None  # type: ignore
    DataFeed = None  # type: ignore
    Adjustment = None  # type: ignore
    TimeFrame = None  # type: ignore
    TimeFrameUnit = None  # type: ignore


class DataFetcher:
    """
    Market data fetcher supporting multiple data sources.
    """

    def __init__(self, provider: str = None):
        """
        Initialize data fetcher.

        Args:
            provider: Data provider ('yfinance', 'alpha_vantage', 'alpaca', etc.)
        """
        self.provider = provider or config.get(
            "market_data.default_provider", "yfinance"
        )
        self.alpha_vantage_api_key = config.get("market_data.alpha_vantage_api_key")

        # Cache placeholders (reserved for future enhancements)
        self.cache: Dict[str, pd.DataFrame] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        self.cache_expiry = timedelta(minutes=15)

        # Alpaca client state
        self._alpaca_client: Optional[StockHistoricalDataClient] = None
        self._alpaca_feed: Optional[DataFeed] = None
        self._alpaca_params: Dict[str, Union[str, bool]] = {}

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
            DataFrame with OHLCV data
        """
        if self.provider == "yfinance":
            return self._fetch_yfinance_data(symbol, start_date, end_date, interval)
        if self.provider == "alpha_vantage":
            return self._fetch_alpha_vantage_data(symbol, start_date, end_date)
        if self.provider == "alpaca":
            return self._fetch_alpaca_data(symbol, start_date, end_date, interval)

        raise ValueError(f"Unsupported provider: {self.provider}")

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
            except (requests.RequestException, ValueError, KeyError, APIError) as exc:
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
        if self.provider == "yfinance":
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info.get("currentPrice", info.get("regularMarketPrice", 0.0))

        if self.provider == "alpaca":
            trade = self._fetch_alpaca_latest_trade(symbol)
            return float(trade["price"]) if trade else 0.0

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
    # Provider implementations
    # ------------------------------------------------------------------ #
    def _fetch_yfinance_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str,
    ) -> pd.DataFrame:
        """Fetch data using yfinance."""
        ticker = yf.Ticker(symbol)

        # Set default dates if not provided
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        data = ticker.history(
            start=start_date,
            end=end_date,
            interval=interval,
            auto_adjust=True,
            prepost=True,
        )

        if data.empty:
            raise ValueError(f"No data found for symbol {symbol}")

        # Standardize column names
        data.columns = [col.lower().replace(" ", "_") for col in data.columns]

        return data

    def _fetch_alpha_vantage_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
    ) -> pd.DataFrame:
        """Fetch data using Alpha Vantage API."""
        if not self.alpha_vantage_api_key:
            raise ValueError("Alpha Vantage API key not configured")

        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "apikey": self.alpha_vantage_api_key,
            "outputsize": "full",
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if "Error Message" in data:
            raise ValueError(f"Alpha Vantage error: {data['Error Message']}")

        if "Time Series (Daily)" not in data:
            raise ValueError(f"No data found for symbol {symbol}")

        df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index")
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)

        df = df.astype(float)
        df.columns = [
            "open",
            "high",
            "low",
            "close",
            "adjusted_close",
            "volume",
            "dividend_amount",
            "split_coefficient",
        ]

        if start_date:
            df = df[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df.index <= pd.to_datetime(end_date)]

        return df

    def _fetch_alpaca_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str,
    ) -> pd.DataFrame:
        """Fetch data using Alpaca market data API."""
        if StockHistoricalDataClient is None or StockBarsRequest is None:
            raise ImportError("alpaca-py is required for the 'alpaca' data provider.")

        client, feed, params = self._ensure_alpaca_client()
        timeframe = self._map_alpaca_interval(interval)

        start_dt = pd.to_datetime(start_date) if start_date else None
        end_dt = pd.to_datetime(end_date) if end_date else None

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=timeframe,
            start=start_dt,
            end=end_dt,
            adjustment=Adjustment.RAW if Adjustment else None,
            feed=feed if hasattr(StockBarsRequest, "feed") else None,  # type: ignore[arg-type]
        )

        bars = client.get_stock_bars(request)
        df = bars.df if hasattr(bars, "df") else pd.DataFrame()
        if df.empty:
            raise ValueError(f"No Alpaca data found for symbol {symbol}")

        if isinstance(df.index, pd.MultiIndex):
            df = df.xs(symbol, level="symbol").copy()
        else:
            df = df.copy()

        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_convert("UTC").tz_localize(None)
        df.index.name = "date"

        # Ensure consistent column naming
        df.columns = [str(col).lower() for col in df.columns]

        return df

    def _fetch_alpaca_latest_trade(self, symbol: str) -> Optional[Dict[str, Union[str, float]]]:
        if StockHistoricalDataClient is None or StockLatestTradeRequest is None:
            raise ImportError("alpaca-py is required for the 'alpaca' data provider.")

        client, feed, _ = self._ensure_alpaca_client()
        try:
            request = StockLatestTradeRequest(symbol_or_symbols=symbol, feed=feed)
            trade = client.get_stock_latest_trade(request)
        except APIError as exc:  # pragma: no cover - depends on remote service
            print(f"Alpaca latest trade error for {symbol}: {exc}")
            return None

        if isinstance(trade, dict):
            entry = trade.get(symbol)
        else:
            entry = trade
        return entry if entry else None

    # ------------------------------------------------------------------ #
    # Alpaca helpers
    # ------------------------------------------------------------------ #
    def _ensure_alpaca_client(
        self,
    ) -> Tuple[StockHistoricalDataClient, DataFeed, Dict[str, Union[str, bool]]]:
        if self._alpaca_client is not None and self._alpaca_feed is not None:
            return self._alpaca_client, self._alpaca_feed, self._alpaca_params

        if StockHistoricalDataClient is None:
            raise ImportError("alpaca-py is required for the 'alpaca' data provider.")

        broker_type, params = config.resolve_broker("alpaca")
        if broker_type != "alpaca":
            raise ValueError("Alpaca market data requires an 'alpaca' broker configuration.")

        api_key = params.get("api_key")
        api_secret = params.get("api_secret")
        if not api_key or not api_secret:
            raise EnvironmentError("Alpaca API credentials are required for market data access.")

        feed_name = str(params.get("data_feed", "iex")).lower()
        sandbox = bool(params.get("paper", True))

        try:
            feed = DataFeed(feed_name) if DataFeed else None
        except Exception as exc:  # pragma: no cover - invalid feed configuration
            raise ValueError(f"Unsupported Alpaca data feed: {feed_name}") from exc

        self._alpaca_client = StockHistoricalDataClient(
            api_key=api_key,
            secret_key=api_secret,
            sandbox=sandbox,
        )
        self._alpaca_feed = feed
        self._alpaca_params = {"paper": sandbox, "data_feed": feed_name}

        return self._alpaca_client, feed, self._alpaca_params

    @staticmethod
    def _map_alpaca_interval(interval: str) -> TimeFrame:
        if TimeFrame is None or TimeFrameUnit is None:
            raise ImportError("alpaca-py is required for the 'alpaca' data provider.")

        interval = interval.lower()

        if interval == "1d":
            return TimeFrame.Day  # type: ignore[return-value]
        if interval == "1h":
            return TimeFrame.Hour  # type: ignore[return-value]
        if interval.endswith("m"):
            value = int(interval[:-1])
            if value == 1:
                return TimeFrame.Minute  # type: ignore[return-value]
            return TimeFrame(value, TimeFrameUnit.Minute)  # type: ignore[call-arg]
        if interval.endswith("h"):
            value = int(interval[:-1])
            if value == 1:
                return TimeFrame.Hour  # type: ignore[return-value]
            return TimeFrame(value, TimeFrameUnit.Hour)  # type: ignore[call-arg]
        if interval.endswith("d"):
            value = int(interval[:-1])
            if value == 1:
                return TimeFrame.Day  # type: ignore[return-value]
            return TimeFrame(value, TimeFrameUnit.Day)  # type: ignore[call-arg]

        raise ValueError(f"Unsupported Alpaca interval: {interval}")
