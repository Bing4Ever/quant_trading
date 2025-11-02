#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Concrete broker implementation backed by Alpaca's REST API.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..interfaces.broker import DatetimeLike, IBroker
from ..models.enums import OrderSide, OrderStatus, OrderType
from ..models.order import Order
from ..models.position import Position

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency for runtime environments
    from alpaca_trade_api.rest import APIError, REST  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully for test environments
    APIError = Exception  # type: ignore
    REST = None  # type: ignore
    _ALPACA_AVAILABLE = False
else:
    _ALPACA_AVAILABLE = True

__all__ = ["AlpacaBroker"]


class AlpacaBroker(IBroker):
    """Broker implementation that talks to Alpaca via the official REST API."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        *,
        paper: bool = True,
        data_feed: str = "iex",
        default_time_in_force: str = "gtc",
        base_url: Optional[str] = None,
    ) -> None:
        if not _ALPACA_AVAILABLE:
            raise ImportError(
                "alpaca-trade-api is required. Install it with `pip install alpaca-trade-api`."
            )

        self.api_key = api_key
        self.api_secret = api_secret
        self.paper = paper
        self._default_tif = (default_time_in_force or "gtc").lower()
        self._data_feed = (data_feed or "iex").lower()
        self._base_url = base_url or self._default_base_url(paper)

        self._client: Optional[REST] = None
        self._connected = False

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def connect(self) -> bool:
        """Initialise the REST client and verify credentials."""
        if not _ALPACA_AVAILABLE:
            raise ImportError("alpaca-trade-api is not installed.")

        try:
            self._client = REST(
                self.api_key,
                self.api_secret,
                base_url=self._base_url,
                api_version="v2",
            )
            self._client.get_account()
            self._connected = True
            logger.info(
                "AlpacaBroker connected (paper=%s, feed=%s)",
                self.paper,
                self._data_feed,
            )
            return True
        except APIError as exc:  # pragma: no cover - depends on remote service
            logger.error("Failed to connect to Alpaca: %s", exc)
            self._client = None
            self._connected = False
            return False

    def disconnect(self) -> bool:
        """Dispose the REST client."""
        self._client = None
        self._connected = False
        logger.info("AlpacaBroker disconnected.")
        return True

    def is_connected(self) -> bool:
        """Return True when the REST client is ready."""
        return self._connected

    # ------------------------------------------------------------------ #
    # Trading operations
    # ------------------------------------------------------------------ #
    def submit_order(self, order: Order) -> bool:
        """Submit an order to Alpaca."""
        client = self._ensure_client()

        side = "buy" if order.side == OrderSide.BUY else "sell"
        tif = self._map_time_in_force(getattr(order, "time_in_force", None))
        order_type = self._map_order_type(order.order_type)
        quantity = abs(int(order.quantity))
        limit_price = getattr(order, "price", None)
        stop_price = getattr(order, "stop_price", None)

        try:
            payload: Dict[str, Any] = {
                "symbol": order.symbol,
                "qty": quantity,
                "side": side,
                "type": order_type,
                "time_in_force": tif,
                "client_order_id": order.order_id,
            }
            if limit_price is not None:
                payload["limit_price"] = limit_price
            if stop_price is not None:
                payload["stop_price"] = stop_price

            response = client.submit_order(**payload)  # type: ignore[call-arg]  # pylint: disable=unexpected-keyword-arg
            self._update_order_from_response(order, response)
            return True
        except APIError as exc:  # pragma: no cover - depends on remote service
            logger.error("Failed to submit Alpaca order (%s): %s", order.symbol, exc)
            order.status = OrderStatus.REJECTED
            return False

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by client identifier."""
        client = self._ensure_client()
        try:
            remote = client.get_order_by_client_order_id(order_id)
        except APIError as exc:  # pragma: no cover
            logger.warning("Failed to locate order (%s): %s", order_id, exc)
            return False

        try:
            client.cancel_order(remote.id)
            return True
        except APIError as exc:  # pragma: no cover
            logger.warning("Failed to cancel order (%s): %s", order_id, exc)
            return False

    def get_order_status(self, order_id: str) -> Optional[Order]:
        """Return the latest status for a client order."""
        client = self._ensure_client()
        try:
            remote = client.get_order_by_client_order_id(order_id)
        except APIError as exc:  # pragma: no cover
            logger.error("Failed to fetch order status (%s): %s", order_id, exc)
            return None

        local = Order(
            order_id=remote.client_order_id or remote.id,
            symbol=remote.symbol,
            side=OrderSide.BUY if remote.side.lower() == "buy" else OrderSide.SELL,
            quantity=int(Decimal(remote.qty)),
            order_type=self._map_api_order_type(remote.type),
            price=float(remote.limit_price) if remote.limit_price is not None else None,
            stop_price=(
                float(remote.stop_price) if remote.stop_price is not None else None
            ),
        )
        self._update_order_from_response(local, remote)
        return local

    def get_account_balance(self) -> Dict[str, float]:
        """Return cash, equity, and buying power values."""
        client = self._ensure_client()
        try:
            account = client.get_account()
        except APIError as exc:  # pragma: no cover
            logger.error("Failed to retrieve account: %s", exc)
            return {"cash": 0.0, "equity": 0.0, "buying_power": 0.0}

        return {
            "cash": float(account.cash),
            "equity": float(account.equity),
            "buying_power": float(account.buying_power),
        }

    def get_positions(self) -> List[Position]:
        """Return the currently open positions."""
        client = self._ensure_client()
        try:
            remote_positions = client.list_positions()
        except APIError as exc:  # pragma: no cover
            logger.error("Failed to fetch positions: %s", exc)
            return []

        positions: List[Position] = []
        for pos in remote_positions:
            quantity = int(Decimal(pos.qty))
            avg_price = float(pos.avg_entry_price)
            current_price = float(pos.current_price)
            market_value = float(pos.market_value)
            unrealized_pnl = float(pos.unrealized_pl)
            pnl_percent = float(pos.unrealized_plpc or 0) * 100.0

            positions.append(
                Position(
                    symbol=pos.symbol,
                    quantity=quantity,
                    average_price=avg_price,
                    current_price=current_price,
                    market_value=market_value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percent=pnl_percent,
                )
            )

        return positions

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Return the latest trade price for the symbol."""
        trade = self.get_latest_trade(symbol)
        if trade is None:
            return None
        return float(trade["price"])

    # ------------------------------------------------------------------ #
    # Market data helpers
    # ------------------------------------------------------------------ #
    def get_latest_trade(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Return the most recent trade for the given symbol."""
        client = self._ensure_client()
        try:
            trade = client.get_latest_trade(symbol, feed=self._data_feed)
        except APIError as exc:  # pragma: no cover
            logger.warning("Failed to get latest trade for %s: %s", symbol, exc)
            return None

        if trade is None:
            return None

        timestamp = getattr(trade, "timestamp", None) or getattr(trade, "t", None)
        if isinstance(timestamp, datetime):
            timestamp_value = timestamp.astimezone(timezone.utc).isoformat()
        else:
            timestamp_value = str(timestamp) if timestamp is not None else None

        size = getattr(trade, "size", None) or getattr(trade, "qty", None)
        price = getattr(trade, "price", None) or getattr(trade, "p", None)

        return {
            "symbol": symbol,
            "price": float(price) if price is not None else None,
            "size": float(size) if size is not None else None,
            "timestamp": timestamp_value,
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
        """Return historical OHLC bars for the symbol."""
        client = self._ensure_client()
        start_dt = self._coerce_datetime(start)
        end_dt = self._coerce_datetime(end)
        timeframe = self._map_interval(interval)

        request_kwargs: Dict[str, Any] = {
            "start": start_dt.isoformat() if start_dt else None,
            "end": end_dt.isoformat() if end_dt else None,
            "adjustment": adjustment,
            "feed": self._data_feed,
        }
        if limit is not None:
            request_kwargs["limit"] = limit

        try:
            bars = client.get_bars(
                symbol,
                timeframe,
                **request_kwargs,
            )
        except APIError as exc:  # pragma: no cover
            logger.error("Failed to fetch bars for %s: %s", symbol, exc)
            return []

        results: List[Dict[str, Any]] = []
        for bar in bars:
            timestamp = getattr(bar, "timestamp", None) or getattr(bar, "t", None)
            if isinstance(timestamp, datetime):
                ts_value = timestamp.astimezone(timezone.utc).isoformat()
            else:
                ts_value = str(timestamp) if timestamp is not None else None

            open_price = getattr(bar, "open", None) or getattr(bar, "o", None)
            high_price = getattr(bar, "high", None) or getattr(bar, "h", None)
            low_price = getattr(bar, "low", None) or getattr(bar, "l", None)
            close_price = getattr(bar, "close", None) or getattr(bar, "c", None)
            volume = getattr(bar, "volume", None) or getattr(bar, "v", None)

            results.append(
                {
                    "symbol": symbol,
                    "timestamp": ts_value,
                    "open": float(open_price) if open_price is not None else None,
                    "high": float(high_price) if high_price is not None else None,
                    "low": float(low_price) if low_price is not None else None,
                    "close": float(close_price) if close_price is not None else None,
                    "volume": float(volume) if volume is not None else None,
                    "trade_count": getattr(bar, "trade_count", None)
                    or getattr(bar, "n", None),
                    "vwap": self._safe_float(
                        getattr(bar, "vwap", None) or getattr(bar, "vw", None)
                    ),
                }
            )

        return results

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _ensure_client(self) -> REST:
        if not self._connected or self._client is None:
            raise RuntimeError("AlpacaBroker is not connected. Call connect() first.")
        return self._client

    @staticmethod
    def _default_base_url(paper: bool) -> str:
        return (
            "https://paper-api.alpaca.markets"
            if paper
            else "https://api.alpaca.markets"
        )

    @staticmethod
    def _map_order_type(order_type: OrderType) -> str:
        mapping = {
            OrderType.MARKET: "market",
            OrderType.LIMIT: "limit",
            OrderType.STOP: "stop",
            OrderType.STOP_LIMIT: "stop_limit",
        }
        return mapping.get(order_type, "market")

    @staticmethod
    def _map_api_order_type(order_type: str) -> OrderType:
        value = (order_type or "").lower()
        mapping = {
            "market": OrderType.MARKET,
            "limit": OrderType.LIMIT,
            "stop": OrderType.STOP,
            "stop_limit": OrderType.STOP_LIMIT,
        }
        return mapping.get(value, OrderType.MARKET)

    def _map_time_in_force(self, value: Optional[str]) -> str:
        raw = (value or self._default_tif).lower()
        mapping = {
            "gtc": "gtc",
            "day": "day",
            "fok": "fok",
            "ioc": "ioc",
            "opg": "opg",
            "cls": "cls",
        }
        return mapping.get(raw, "gtc")

    @staticmethod
    def _map_order_status(status: str) -> OrderStatus:
        mapping = {
            "new": OrderStatus.PENDING,
            "accepted": OrderStatus.PENDING,
            "pending_new": OrderStatus.PENDING,
            "partially_filled": getattr(
                OrderStatus, "PARTIAL_FILLED", OrderStatus.FILLED
            ),
            "filled": OrderStatus.FILLED,
            "done_for_day": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED,
            "pending_cancel": OrderStatus.CANCELLED,
            "pending_replace": OrderStatus.PENDING,
            "replaced": OrderStatus.FILLED,
            "rejected": OrderStatus.REJECTED,
            "expired": OrderStatus.CANCELLED,
            "stopped": OrderStatus.CANCELLED,
            "suspended": OrderStatus.CANCELLED,
        }
        return mapping.get(status.lower(), OrderStatus.PENDING)

    def _update_order_from_response(self, order: Order, response: Any) -> None:
        status_value = getattr(response, "status", "")
        order.status = self._map_order_status(str(status_value))

        filled_qty = getattr(response, "filled_qty", None)
        if filled_qty is not None:
            order.filled_quantity = int(Decimal(str(filled_qty)))

        filled_price = getattr(response, "filled_avg_price", None)
        if filled_price is not None:
            order.filled_price = float(filled_price)

        submitted_at = getattr(response, "submitted_at", None)
        if isinstance(submitted_at, datetime):
            order.timestamp = submitted_at.astimezone(timezone.utc)

    @staticmethod
    def _map_interval(interval: str) -> str:
        raw = (interval or "").lower()
        if raw.endswith("m"):
            minutes = raw[:-1]
            return f"{minutes}Min"
        if raw.endswith("h"):
            hours = raw[:-1]
            return f"{hours}Hour"
        if raw.endswith("d"):
            days = raw[:-1]
            return f"{days}Day"
        mapping = {
            "1": "1Day",
            "day": "1Day",
            "1min": "1Min",
            "1m": "1Min",
            "1h": "1Hour",
        }
        return mapping.get(raw, "1Day")

    @staticmethod
    def _coerce_datetime(value: Optional[DatetimeLike]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            dt = value
        else:
            cleaned = value.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(cleaned)
            except ValueError:
                # Fallback for simple dates such as YYYY-MM-DD
                dt = datetime.strptime(cleaned.split("T")[0], "%Y-%m-%d")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
