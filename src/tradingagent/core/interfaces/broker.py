#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Broker Interface - 经纪商接口定义

定义经纪商的抽象接口，规范所有经纪商实现必须遵循的契约。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from ..models import Order, Position


class IBroker(ABC):
    """经纪商接口抽象基类"""
    
    @abstractmethod
    def connect(self) -> bool:
        """
        连接到经纪商
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        断开与经纪商的连接
        
        Returns:
            bool: 断开是否成功
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        检查是否已连接
        
        Returns:
            bool: 是否已连接
        """
        pass
    
    @abstractmethod
    def submit_order(self, order: Order) -> bool:
        """
        提交订单
        
        Args:
            order: 订单对象
            
        Returns:
            bool: 提交是否成功
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            bool: 取消是否成功
        """
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """
        查询订单状态
        
        Args:
            order_id: 订单ID
            
        Returns:
            Order: 订单对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_account_balance(self) -> Dict[str, float]:
        """
        获取账户余额
        
        Returns:
            Dict: 账户余额信息
                - cash: 现金余额
                - equity: 总权益
                - buying_power: 购买力
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """
        获取持仓信息
        
        Returns:
            List[Position]: 持仓列表
        """
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        获取当前价格
        
        Args:
            symbol: 股票代码
            
        Returns:
            float: 当前价格，如果无法获取则返回None
        """
        pass
