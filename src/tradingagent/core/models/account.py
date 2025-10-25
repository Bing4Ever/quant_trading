#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Account Model - 账户数据模型

定义账户和余额相关的数据结构。
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Balance:
    """余额数据类"""
    cash: float
    equity: float
    buying_power: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'cash': self.cash,
            'equity': self.equity,
            'buying_power': self.buying_power
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Balance':
        """从字典创建余额"""
        return cls(
            cash=data.get('cash', 0.0),
            equity=data.get('equity', 0.0),
            buying_power=data.get('buying_power', 0.0)
        )


@dataclass
class Account:
    """账户数据类"""
    account_id: str
    balance: Balance
    initial_capital: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'account_id': self.account_id,
            'balance': self.balance.to_dict(),
            'initial_capital': self.initial_capital
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Account':
        """从字典创建账户"""
        return cls(
            account_id=data['account_id'],
            balance=Balance.from_dict(data['balance']),
            initial_capital=data.get('initial_capital', 0.0)
        )
