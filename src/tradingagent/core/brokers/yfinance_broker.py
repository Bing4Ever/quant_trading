#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Broker implementation backed by yfinance market data.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import yfinance as yf

from ..interfaces.broker import DatetimeLike, IBroker
from ..models.order import Order
from ..models.position import Position

logger = logging.getLogger(__name__)


class YFinanceBroker(IBroker):
    """
    Lightweight broker facade that surfaces yfinance market data through the
    IBroker interface. Trading operations are not supported.
    """

    def __init__(self, *, auto_adjust: bool = True, prepost: bool = True) -> None:
        self.auto_adjust = auto_adjust
        self.prepost = prepost
        self._connected = False

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def connect(self) -> bool:
        self._connected = True
        logger.debug("YFinanceBroker connected")
        return True

    def disconnect(self) -> bool:
        self._connected = False
        logger.debug("YFinanceBroker disconnected")
        return True

    def is_connected(self) -> bool:
        return self._connected

    # ------------------------------------------------------------------ #
    # Trading operations (unsupported)
    # ------------------------------------------------------------------ #
    def submit_order(self, order: Order) -> bool:
        raise NotImplementedError("YFinanceBroker does not support order submission.")

    def cancel_order(self, order_id: str) -> bool:
        raise NotImplementedError("YFinanceBroker does not support cancelling orders.")

    def get_order_status(self, order_id: str) -> Optional[Order]:
        raise NotImplementedError("YFinanceBroker does not support order queries.")

    def get_account_balance(self) -> Dict[str, float]:
        raise NotImplementedError("YFinanceBroker does not track account balances.")

    def get_positions(self) -> List[Position]:
        raise NotImplementedError("YFinanceBroker does not track positions.")

    # ------------------------------------------------------------------ #
    # Market data operations
    # ------------------------------------------------------------------ #
    def get_current_price(self, symbol: str) -> Optional[float]:
        ticker = yf.Ticker(symbol)
        price = None

        fast_info = getattr(ticker, "fast_info", None)
        if fast_info is not None:
            price = getattr(fast_info, "last_price", None) or getattr(
                fast_info, "lastPrice", None
            )

        if price is None:
            history = ticker.history(
                period="1d",
                interval="1m",
                auto_adjust=self.auto_adjust,
                prepost=self.prepost,
            )
            if not history.empty:
                price = float(history["Close"].iloc[-1])

        return float(price) if price is not None else None

    def get_latest_trade(self, symbol: str) -> Optional[Dict[str, Any]]:
        ticker = yf.Ticker(symbol)
        history = ticker.history(
            period="1d",
            interval="1m",
            auto_adjust=self.auto_adjust,
            prepost=self.prepost,
        )
        if history.empty:
            return None

        row = history.iloc[-1]
        timestamp = history.index[-1]
        timestamp = self._normalize_timestamp(timestamp)

        return {
            "symbol": symbol,
            "price": float(row["Close"]),
            "size": float(row.get("Volume", 0) or 0),
            "timestamp": timestamp.isoformat(),
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
        ticker = yf.Ticker(symbol)
        params: Dict[str, Any] = {
            "interval": interval,
            "auto_adjust": self.auto_adjust,
            "prepost": self.prepost,
        }

        start_dt = self._coerce_datetime(start)
        end_dt = self._coerce_datetime(end)

        if start_dt is not None:
            params["start"] = start_dt
        if end_dt is not None:
            params["end"] = end_dt

        history = ticker.history(**params)
        if history.empty:
            return []

        if limit is not None and len(history) > limit:
            history = history.tail(limit)

        records: List[Dict[str, Any]] = []
        for timestamp, row in history.iterrows():
            ts = self._normalize_timestamp(timestamp)
            records.append(
                {
                    "symbol": symbol,
                    "timestamp": ts.isoformat(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row.get("Volume", 0) or 0),
                    "trade_count": None,
                    "vwap": None,
                }
            )

        return records

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _coerce_datetime(value: Optional[DatetimeLike]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value))

    @staticmethod
    def _normalize_timestamp(value: Any) -> datetime:
        if isinstance(value, pd.Timestamp):
            ts = value.to_pydatetime()
        elif isinstance(value, datetime):
            ts = value
        else:
            ts = datetime.fromisoformat(str(value))

        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)


__all__ = ["YFinanceBroker"]
