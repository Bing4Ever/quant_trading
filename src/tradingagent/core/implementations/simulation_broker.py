#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulation Broker Implementation - 模拟经纪商实现

用于回测和模拟交易的经纪商实现。
"""

from typing import Dict, List, Optional, Any

from ..interfaces import IBroker
from ..models import Order, Position, OrderStatus, OrderSide


class SimulationBroker(IBroker):
    """模拟经纪商 - 用于回测和模拟交易"""
    
    def __init__(self, initial_capital: float = 100000.0, commission_rate: float = 0.001):
        """
        初始化模拟经纪商
        
        Args:
            initial_capital: 初始资金
            commission_rate: 手续费率
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_rate = commission_rate
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        self._connected = False
    
    def connect(self) -> bool:
        """连接模拟经纪商"""
        self._connected = True
        return True
    
    def disconnect(self) -> bool:
        """断开模拟经纪商"""
        self._connected = False
        return True
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
    
    def submit_order(self, order: Order) -> bool:
        """
        提交订单（模拟执行）
        
        Args:
            order: 订单对象
            
        Returns:
            bool: 是否成功
        """
        if not self._connected:
            return False
        
        # 获取当前价格
        current_price = self.get_current_price(order.symbol)
        if current_price is None:
            order.status = OrderStatus.REJECTED
            self.orders[order.order_id] = order
            return False
        
        # 计算交易金额和手续费
        trade_amount = current_price * order.quantity
        commission = trade_amount * self.commission_rate
        
        if order.side == OrderSide.BUY:
            # 检查资金是否足够
            total_cost = trade_amount + commission
            if self.cash < total_cost:
                order.status = OrderStatus.REJECTED
                self.orders[order.order_id] = order
                return False
            
            # 执行买入
            self.cash -= total_cost
            if order.symbol not in self.positions:
                self.positions[order.symbol] = {
                    'quantity': 0,
                    'average_price': 0.0
                }
            
            pos = self.positions[order.symbol]
            total_quantity = pos['quantity'] + order.quantity
            pos['average_price'] = (
                (pos['quantity'] * pos['average_price'] + trade_amount) / total_quantity
            )
            pos['quantity'] = total_quantity
            
        else:  # SELL
            # 检查持仓是否足够
            if order.symbol not in self.positions:
                order.status = OrderStatus.REJECTED
                self.orders[order.order_id] = order
                return False
            
            pos = self.positions[order.symbol]
            if pos['quantity'] < order.quantity:
                order.status = OrderStatus.REJECTED
                self.orders[order.order_id] = order
                return False
            
            # 执行卖出
            self.cash += trade_amount - commission
            pos['quantity'] -= order.quantity
            
            # 如果持仓清空则删除
            if pos['quantity'] == 0:
                del self.positions[order.symbol]
        
        # 更新订单状态
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.filled_price = current_price
        self.orders[order.order_id] = order
        self.order_history.append(order)
        
        return True
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.CANCELLED
                return True
        return False
    
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """查询订单状态"""
        return self.orders.get(order_id)
    
    def get_account_balance(self) -> Dict[str, float]:
        """获取账户余额"""
        equity = self.cash
        for symbol, pos in self.positions.items():
            current_price = self.get_current_price(symbol)
            if current_price:
                equity += current_price * pos['quantity']
        
        return {
            'cash': self.cash,
            'equity': equity,
            'buying_power': self.cash
        }
    
    def get_positions(self) -> List[Position]:
        """获取持仓信息"""
        positions = []
        for symbol, pos in self.positions.items():
            current_price = self.get_current_price(symbol)
            if current_price:
                quantity = pos['quantity']
                avg_price = pos['average_price']
                market_value = current_price * quantity
                unrealized_pnl = (current_price - avg_price) * quantity
                unrealized_pnl_percent = (
                    (unrealized_pnl / (avg_price * quantity)) * 100
                )
                
                positions.append(Position(
                    symbol=symbol,
                    quantity=quantity,
                    average_price=avg_price,
                    current_price=current_price,
                    market_value=market_value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percent=unrealized_pnl_percent
                ))
        
        return positions
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        获取当前价格（模拟）
        
        在实际使用中，这里应该从数据源获取实时价格
        """
        # TODO: 集成实时数据源
        return None
