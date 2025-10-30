#!/usr/bin/env python3
"""
实时行情监控相关的基础数据模型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class MarketData:
    """用于承载增量行情数据的简单数据结构。"""

    symbol: str
    price: float
    volume: int
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None


@dataclass
class TradingSignal:
    """用于描述交易信号的基础结构。"""

    symbol: str
    signal_type: str  # BUY / SELL / HOLD
    strength: float
    price: float
    timestamp: datetime
    strategy_name: str
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

