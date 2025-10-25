#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Position Model - 持仓数据模型

定义持仓相关的数据结构。
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Position:
    """持仓数据类"""
    symbol: str
    quantity: int
    average_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'average_price': self.average_price,
            'current_price': self.current_price,
            'market_value': self.market_value,
            'unrealized_pnl': self.unrealized_pnl,
            'unrealized_pnl_percent': self.unrealized_pnl_percent
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Position':
        """从字典创建持仓"""
        return cls(
            symbol=data['symbol'],
            quantity=data['quantity'],
            average_price=data['average_price'],
            current_price=data['current_price'],
            market_value=data['market_value'],
            unrealized_pnl=data['unrealized_pnl'],
            unrealized_pnl_percent=data['unrealized_pnl_percent']
        )
