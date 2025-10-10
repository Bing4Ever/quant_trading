"""
Data fetcher for retrieving market data from various sources.
"""

import time
from typing import List, Dict, Union
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import requests
from config import config


class DataFetcher:
    """
    Market data fetcher supporting multiple data sources.
    """

    def __init__(self, provider: str = None):
        """
        Initialize data fetcher.

        Args:
            provider: Data provider ('yfinance', 'alpha_vantage', etc.)
        """
        self.provider = provider or config.get(
            "market_data.default_provider", "yfinance"
        )
        self.alpha_vantage_api_key = config.get("market_data.alpha_vantage_api_key")

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
        elif self.provider == "alpha_vantage":
            return self._fetch_alpha_vantage_data(symbol, start_date, end_date)
        else:
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
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.fetch_stock_data(
                    symbol, start_date, end_date, interval
                )
                time.sleep(0.1)  # Rate limiting
            except (requests.RequestException, ValueError, KeyError) as e:
                print(f"Error fetching data for {symbol}: {e}")
                results[symbol] = pd.DataFrame()

        return results

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

        # Convert to DataFrame
        df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index")

        # Convert index to datetime
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)

        # Convert columns to numeric and rename
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

        # Filter by date range
        if start_date:
            df = df[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df.index <= pd.to_datetime(end_date)]

        return df

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
        else:
            # Fallback to latest close price
            data = self.fetch_stock_data(
                symbol, start_date=datetime.now() - timedelta(days=5)
            )
            return data["close"].iloc[-1] if not data.empty else 0.0
