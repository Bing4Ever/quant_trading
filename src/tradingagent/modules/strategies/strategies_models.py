"""
Strategy data models.

Shared dataclasses representing strategy execution results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

import pandas as pd


class SignalType(Enum):
    """Trading signal types."""

    BUY = 1
    SELL = -1
    HOLD = 0


class Position(Enum):
    """Position direction types."""

    LONG = 1
    SHORT = -1
    FLAT = 0


@dataclass
class StrategyResult:
    """Strategy execution summary."""

    strategy_name: str
    symbol: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    avg_trade_return: float
    volatility: float
    calmar_ratio: float
    sortino_ratio: float
    trades: List[Dict[str, Any]] = field(default_factory=list)
    signals: pd.DataFrame = field(default_factory=pd.DataFrame)
    portfolio_value: pd.Series = field(default_factory=pd.Series)
    metadata: Dict[str, Any] = field(default_factory=dict)
