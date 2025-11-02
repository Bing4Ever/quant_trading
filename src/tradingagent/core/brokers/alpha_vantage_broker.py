#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Broker implementation that wraps Alpha Vantage market data endpoints.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import requests

from ..interfaces.broker import DatetimeLike, IBroker
from ..models.order import Order
from ..models.position import Position

logger = logging.getLogger(__name__)

INTRADAY_ALLOWED_INTERVALS = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "60m": "60min",
    "1h": "60min",
}


class AlphaVantageBroker(IBroker):
    """
    Alpha Vantage powered broker facade for market data retrieval.
    Trading operations are not supported.
    """

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("Alpha Vantage API key is required.")
        self.api_key = api_key
        self._connected = False
        self._session = requests.Session()

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def connect(self) -> bool:
        if self._connected:
            return True
        self._session = requests.Session()
        self._connected = True
        logger.debug("AlphaVantageBroker connected")
        return True

    def disconnect(self) -> bool:
        self._session.close()
        self._connected = False
        logger.debug("AlphaVantageBroker disconnected")
        return True

    def is_connected(self) -> bool:
        return self._connected

    # ------------------------------------------------------------------ #
    # Trading operations (unsupported)
    # ------------------------------------------------------------------ #
    def submit_order(self, order: Order) -> bool:
        raise NotImplementedError(
            "AlphaVantageBroker does not support order submission."
        )

    def cancel_order(self, order_id: str) -> bool:
        raise NotImplementedError(
            "AlphaVantageBroker does not support cancelling orders."
        )

    def get_order_status(self, order_id: str) -> Optional[Order]:
        raise NotImplementedError("AlphaVantageBroker does not support order queries.")

    def get_account_balance(self) -> Dict[str, float]:
        raise NotImplementedError("AlphaVantageBroker does not track account balances.")

    def get_positions(self) -> List[Position]:
        raise NotImplementedError("AlphaVantageBroker does not track positions.")

    # ------------------------------------------------------------------ #
    # Market data operations
    # ------------------------------------------------------------------ #
    def get_current_price(self, symbol: str) -> Optional[float]:
        payload = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key,
        }
        response = self._request(payload)
        quote = response.get("Global Quote") or {}
        price = quote.get("05. price")
        if price is None:
            return None
        try:
            return float(price)
        except (TypeError, ValueError):
            return None

    def get_latest_trade(self, symbol: str) -> Optional[Dict[str, Any]]:
        payload = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key,
        }
        response = self._request(payload)
        quote = response.get("Global Quote") or {}
        price = quote.get("05. price")
        timestamp = quote.get("07. latest trading day")

        if price is None or timestamp is None:
            return None

        try:
            ts = datetime.fromisoformat(str(timestamp))
        except ValueError:
            ts = datetime.now(timezone.utc)

        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        try:
            price_value = float(price)
        except (TypeError, ValueError):
            return None

        return {
            "symbol": symbol,
            "price": price_value,
            "size": None,
            "timestamp": ts.astimezone(timezone.utc).isoformat(),
        }

    def get_historical_bars(
        self,
        symbol: str,
        start: Optional[DatetimeLike],
        end: Optional[DatetimeLike],
        interval: str,
        *,
        adjustment: str = "raw",
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        interval = interval.lower()
        if interval.endswith("d"):
            data = self._fetch_daily(symbol)
        elif interval in INTRADAY_ALLOWED_INTERVALS:
            alpha_interval = INTRADAY_ALLOWED_INTERVALS[interval]
            data = self._fetch_intraday(symbol, alpha_interval)
        else:
            raise ValueError(f"Unsupported Alpha Vantage interval: {interval}")

        start_dt = self._coerce_datetime(start)
        end_dt = self._coerce_datetime(end)

        records: List[Dict[str, Any]] = []
        for timestamp_str, values in data.items():
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except ValueError:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            else:
                timestamp = timestamp.astimezone(timezone.utc)

            if start_dt and timestamp < start_dt:
                continue
            if end_dt and timestamp > end_dt:
                continue

            records.append(
                {
                    "symbol": symbol,
                    "timestamp": timestamp.isoformat(),
                    "open": float(values.get("1. open", 0.0)),
                    "high": float(values.get("2. high", 0.0)),
                    "low": float(values.get("3. low", 0.0)),
                    "close": float(values.get("4. close", 0.0)),
                    "volume": float(
                        values.get("5. volume") or values.get("6. volume") or 0.0
                    ),
                    "trade_count": None,
                    "vwap": None,
                }
            )

        records.sort(key=lambda entry: entry["timestamp"])
        if limit is not None and len(records) > limit:
            records = records[-limit:]

        return records

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _fetch_daily(self, symbol: str) -> Dict[str, Dict[str, str]]:
        payload = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": "full",
            "apikey": self.api_key,
        }
        response = self._request(payload)
        data = response.get("Time Series (Daily)")
        if not data:
            raise ValueError(f"No Alpha Vantage daily data for {symbol}")
        return data

    def _fetch_intraday(self, symbol: str, interval: str) -> Dict[str, Dict[str, str]]:
        payload = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "outputsize": "full",
            "apikey": self.api_key,
        }
        response = self._request(payload)
        key = f"Time Series ({interval})"
        data = response.get(key)
        if not data:
            raise ValueError(
                f"No Alpha Vantage intraday data for {symbol} ({interval})"
            )
        return data

    def _request(self, params: Dict[str, str]) -> Dict[str, Any]:
        url = "https://www.alphavantage.co/query"
        resp = self._session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        if "Error Message" in payload:
            raise ValueError(payload["Error Message"])
        if "Note" in payload:
            logger.warning("Alpha Vantage notice: %s", payload["Note"])
        return payload

    @staticmethod
    def _coerce_datetime(value: Optional[DatetimeLike]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            result = value
        else:
            try:
                result = datetime.fromisoformat(str(value))
            except ValueError:
                result = datetime.strptime(str(value), "%Y-%m-%d")
        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)
        return result


__all__ = ["AlphaVantageBroker"]
