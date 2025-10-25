#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Signal Model - 交易信号数据模型

定义交易信号相关的数据结构。
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

from .enums import OrderType


@dataclass
class TradingSignal:
    """交易信号数据类"""
    symbol: str
    strategy: str
    action: str  # 'buy' or 'sell'
    quantity: int
    price: Optional[float] = None
    order_type: OrderType = OrderType.MARKET
    timestamp: Optional[datetime] = None
    reason: str = ""
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'strategy': self.strategy,
            'action': self.action,
            'quantity': self.quantity,
            'price': self.price,
            'order_type': self.order_type.value,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'reason': self.reason,
            'confidence': self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingSignal':
        """从字典创建信号"""
        return cls(
            symbol=data['symbol'],
            strategy=data['strategy'],
            action=data['action'],
            quantity=data['quantity'],
            price=data.get('price'),
            order_type=OrderType(data.get('order_type', 'market')),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None,
            reason=data.get('reason', ''),
            confidence=data.get('confidence', 0.0)
        )
