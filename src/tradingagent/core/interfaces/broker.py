#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Abstract broker interface definition.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from ..models import Order, Position

DatetimeLike = Union[str, datetime]

__all__ = ["IBroker", "DatetimeLike"]


class IBroker(ABC):
    """Contract all broker implementations must follow."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish a connection to the remote broker."""

    @abstractmethod
    def disconnect(self) -> bool:
        """Tear down the connection to the remote broker."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Return True when the broker connection is active."""

    @abstractmethod
    def submit_order(self, order: Order) -> bool:
        """Submit an order to the broker."""

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order using the client-defined identifier."""

    @abstractmethod
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """Return the latest known state for the given order."""

    @abstractmethod
    def get_account_balance(self) -> Dict[str, float]:
        """Return a dictionary with cash, equity, and buying power."""

    @abstractmethod
    def get_positions(self) -> List[Position]:
        """Return the list of currently open positions."""

    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Return the most recent trade price for the symbol."""

    @abstractmethod
    def get_latest_trade(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Return the most recent trade snapshot for the symbol."""

    @abstractmethod
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
        """Return historical bar data for the symbol."""
