#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
In-memory broker implementation used for simulations and testing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..interfaces.broker import DatetimeLike, IBroker
from ..interfaces.data_provider import IDataProvider
from ..models.enums import OrderSide, OrderStatus
from ..models.order import Order
from ..models.position import Position

__all__ = ["SimulationBroker"]


class SimulationBroker(IBroker):
    """Simple broker that simulates executions against in-memory state."""

    def __init__(
        self,
        initial_capital: float = 100_000.0,
        commission_rate: float = 0.001,
        data_provider: Optional[IDataProvider] = None,
    ) -> None:
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_rate = commission_rate
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        self._connected = False
        self.data_provider = data_provider

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> bool:
        self._connected = False
        return True

    def is_connected(self) -> bool:
        return self._connected

    # ------------------------------------------------------------------ #
    # Trading operations
    # ------------------------------------------------------------------ #
    def submit_order(self, order: Order) -> bool:
        if not self._connected:
            return False

        current_price = self.get_current_price(order.symbol)
        if current_price is None:
            order.status = OrderStatus.REJECTED
            self.orders[order.order_id] = order
            return False

        trade_amount = current_price * order.quantity
        commission = trade_amount * self.commission_rate

        if order.side == OrderSide.BUY:
            total_cost = trade_amount + commission
            if self.cash < total_cost:
                order.status = OrderStatus.REJECTED
                self.orders[order.order_id] = order
                return False

            self.cash -= total_cost
            position = self.positions.setdefault(
                order.symbol, {"quantity": 0, "average_price": 0.0}
            )
            new_quantity = position["quantity"] + order.quantity
            if new_quantity <= 0:
                position["quantity"] = 0
                position["average_price"] = 0.0
            else:
                position["average_price"] = (
                    position["quantity"] * position["average_price"] + trade_amount
                ) / new_quantity
                position["quantity"] = new_quantity
        else:  # SELL
            position = self.positions.get(order.symbol)
            if position is None or position["quantity"] < order.quantity:
                order.status = OrderStatus.REJECTED
                self.orders[order.order_id] = order
                return False

            self.cash += trade_amount - commission
            position["quantity"] -= order.quantity
            if position["quantity"] == 0:
                del self.positions[order.symbol]

        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.filled_price = current_price
        self.orders[order.order_id] = order
        self.order_history.append(order)
        return True

    def cancel_order(self, order_id: str) -> bool:
        order = self.orders.get(order_id)
        if order and order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CANCELLED
            return True
        return False

    def get_order_status(self, order_id: str) -> Optional[Order]:
        return self.orders.get(order_id)

    def get_account_balance(self) -> Dict[str, float]:
        equity = self.cash
        for symbol, position in self.positions.items():
            price = self.get_current_price(symbol)
            if price is not None:
                equity += price * position["quantity"]
        return {"cash": self.cash, "equity": equity, "buying_power": self.cash}

    def get_positions(self) -> List[Position]:
        positions: List[Position] = []
        for symbol, data in self.positions.items():
            current_price = self.get_current_price(symbol)
            if current_price is None:
                continue
            quantity = data["quantity"]
            avg_price = data["average_price"]
            market_value = current_price * quantity
            unrealized_pnl = (current_price - avg_price) * quantity
            denom = avg_price * quantity
            unrealized_pct = (unrealized_pnl / denom) * 100 if denom else 0.0

            positions.append(
                Position(
                    symbol=symbol,
                    quantity=quantity,
                    average_price=avg_price,
                    current_price=current_price,
                    market_value=market_value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percent=unrealized_pct,
                )
            )
        return positions

    def get_current_price(self, symbol: str) -> Optional[float]:
        if self.data_provider is None:
            return None
        try:
            return self.data_provider.get_current_price(symbol)
        except Exception:  # pragma: no cover - provider specific
            return None

    def get_latest_trade(self, symbol: str) -> Optional[Dict[str, Any]]:
        price = self.get_current_price(symbol)
        if price is None:
            return None
        return {
            "symbol": symbol,
            "price": float(price),
            "size": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
        if self.data_provider is None:
            return []

        start_value = self._format_datetime_like(start)
        end_value = self._format_datetime_like(end)

        try:
            frame = self.data_provider.get_historical_data(
                symbol, start_value, end_value, interval
            )
        except Exception:  # pragma: no cover - provider specific
            return []

        if frame is None:
            return []

        if limit is not None and hasattr(frame, "tail"):
            frame = frame.tail(limit)

        records: List[Dict[str, Any]] = []
        iter_rows = frame.iterrows() if hasattr(frame, "iterrows") else []
        for index, row in iter_rows:
            records.append(
                {
                    "symbol": symbol,
                    "timestamp": self._format_timestamp(index),
                    "open": self._safe_float(
                        self._extract_row_value(row, ("open", "Open"))
                    ),
                    "high": self._safe_float(
                        self._extract_row_value(row, ("high", "High"))
                    ),
                    "low": self._safe_float(
                        self._extract_row_value(row, ("low", "Low"))
                    ),
                    "close": self._safe_float(
                        self._extract_row_value(row, ("close", "Close"))
                    ),
                    "volume": self._safe_float(
                        self._extract_row_value(row, ("volume", "Volume"))
                    ),
                    "trade_count": None,
                    "vwap": None,
                }
            )

        return records

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _format_datetime_like(value: Optional[DatetimeLike]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return str(value)

    @staticmethod
    def _format_timestamp(value: Any) -> Optional[str]:
        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()  # type: ignore[call-arg]
            except TypeError:
                return str(value)
        return str(value) if value is not None else None

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _extract_row_value(row: Any, candidates: Tuple[str, ...]) -> Any:
        getter = getattr(row, "get", None)
        for key in candidates:
            if getter is not None:
                value = getter(key)
            else:
                try:
                    value = row[key]  # type: ignore[index]
                except Exception:
                    value = None
            if value is not None:
                return value
        return None
