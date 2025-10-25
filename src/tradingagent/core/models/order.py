#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Order Model - 订单数据模型

定义订单相关的数据结构。
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime

from .enums import OrderType, OrderSide, OrderStatus


@dataclass
class Order:
    """订单数据类"""
    order_id: str
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    filled_price: Optional[float] = None
    timestamp: Optional[datetime] = None
    strategy: str = ""
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'quantity': self.quantity,
            'order_type': self.order_type.value,
            'price': self.price,
            'status': self.status.value,
            'filled_quantity': self.filled_quantity,
            'filled_price': self.filled_price,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'strategy': self.strategy
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """从字典创建订单"""
        return cls(
            order_id=data['order_id'],
            symbol=data['symbol'],
            side=OrderSide(data['side']),
            quantity=data['quantity'],
            order_type=OrderType(data['order_type']),
            price=data.get('price'),
            status=OrderStatus(data.get('status', 'pending')),
            filled_quantity=data.get('filled_quantity', 0),
            filled_price=data.get('filled_price'),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None,
            strategy=data.get('strategy', '')
        )
