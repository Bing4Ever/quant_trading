#!/usr/bin/env python3

import time
import threading
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from enum import Enum
from dataclasses import dataclass, field
import json
import queue
from abc import ABC, abstractmethod

from utils.logger import TradingLogger
from utils.notification import NotificationManager
from data.database import BacktestDatabase


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"
    PARTIAL_FILLED = "partial_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class TradingMode(Enum):
    """交易模式"""
    SIMULATION = "simulation"
    LIVE = "live"


@dataclass
class TradingSignal:
    """交易信号"""
    symbol: str
    strategy: str
    action: str  # 'buy' or 'sell'
    quantity: int
    price: Optional[float] = None
    order_type: OrderType = OrderType.MARKET
    timestamp: datetime = field(default_factory=datetime.now)
    reason: str = ""
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'strategy': self.strategy,
            'action': self.action,
            'quantity': self.quantity,
            'price': self.price,
            'order_type': self.order_type.value,
            'timestamp': self.timestamp.isoformat(),
            'reason': self.reason,
            'confidence': self.confidence
        }


@dataclass
class TradeOrder:
    """交易订单"""
    id: str
    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    filled_price: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    strategy: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side.value,
            'quantity': self.quantity,
            'order_type': self.order_type.value,
            'price': self.price,
            'status': self.status.value,
            'filled_quantity': self.filled_quantity,
            'filled_price': self.filled_price,
            'timestamp': self.timestamp.isoformat(),
            'strategy': self.strategy
        }


class BrokerInterface(ABC):
    """券商接口抽象基类"""
    
    @abstractmethod
    def connect(self) -> bool:
        """连接券商API"""
        raise NotImplementedError
    
    @abstractmethod
    def disconnect(self) -> bool:
        """断开连接"""
        raise NotImplementedError
    
    @abstractmethod
    def place_order(self, order: TradeOrder) -> str:
        """下单"""
        raise NotImplementedError
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        raise NotImplementedError
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> OrderStatus:
        """获取订单状态"""
        raise NotImplementedError
    
    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        raise NotImplementedError
    
    @abstractmethod
    def get_positions(self) -> Dict[str, Any]:
        """获取持仓信息"""
        raise NotImplementedError


class SimulationBroker(BrokerInterface):
    """模拟券商"""
    
    def __init__(self, initial_cash: float = 100000.0):
        self.logger = TradingLogger(__name__)
        self.connected = False
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions = {}  # {symbol: quantity}
        self.orders = {}  # {order_id: TradeOrder}
        self.order_counter = 0
        
    def connect(self) -> bool:
        """连接模拟券商"""
        self.connected = True
        self.logger.log_system_event("模拟券商连接", "连接成功")
        return True
    
    def disconnect(self) -> bool:
        """断开连接"""
        self.connected = False
        self.logger.log_system_event("模拟券商断开", "断开连接")
        return True
    
    def place_order(self, order: TradeOrder) -> str:
        """下单"""
        if not self.connected:
            raise ConnectionError("Not connected to broker")
        
        # 生成订单ID
        self.order_counter += 1
        order.id = f"SIM_{self.order_counter:06d}"
        
        # 模拟订单执行
        if order.order_type == OrderType.MARKET:
            # 市价单立即执行
            execution_price = self._get_market_price(order.symbol)
            if self._validate_order(order, execution_price):
                self._execute_order(order, execution_price)
                order.status = OrderStatus.FILLED
            else:
                order.status = OrderStatus.REJECTED
        else:
            # 限价单等其他类型暂时简化处理
            order.status = OrderStatus.PENDING
        
        self.orders[order.id] = order
        
        self.logger.log_trade_execution(
            order.symbol, 
            order.side.value, 
            order.quantity, 
            order.filled_price or 0, 
            order.id
        )
        
        return order.id
    
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.CANCELLED
                self.logger.log_system_event("撤单", f"订单 {order_id} 已撤销")
                return True
        return False
    
    def get_order_status(self, order_id: str) -> OrderStatus:
        """获取订单状态"""
        if order_id in self.orders:
            return self.orders[order_id].status
        return OrderStatus.REJECTED
    
    def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        total_value = self.cash
        for symbol, quantity in self.positions.items():
            if quantity > 0:
                market_price = self._get_market_price(symbol)
                total_value += quantity * market_price
        
        return {
            'cash': self.cash,
            'total_value': total_value,
            'positions_count': len([p for p in self.positions.values() if p > 0]),
            'buying_power': self.cash
        }
    
    def get_positions(self) -> Dict[str, Any]:
        """获取持仓信息"""
        positions = {}
        for symbol, quantity in self.positions.items():
            if quantity > 0:
                market_price = self._get_market_price(symbol)
                positions[symbol] = {
                    'quantity': quantity,
                    'market_price': market_price,
                    'market_value': quantity * market_price
                }
        return positions
    
    def _get_market_price(self, symbol: str) -> float:
        """获取市场价格（模拟）"""
        # 简化的价格模拟，实际应该连接真实数据源
        import random
        base_prices = {
            'AAPL': 150.0,
            'MSFT': 300.0,
            'GOOGL': 2500.0,
            'TSLA': 800.0,
            'AMZN': 3000.0
        }
        base_price = base_prices.get(symbol, 100.0)
        # 添加随机波动
        return base_price * (1 + random.uniform(-0.02, 0.02))
    
    def _validate_order(self, order: TradeOrder, price: float) -> bool:
        """验证订单"""
        if order.side == OrderSide.BUY:
            # 检查现金是否足够
            required_cash = order.quantity * price
            return self.cash >= required_cash
        else:  # SELL
            # 检查持仓是否足够
            current_position = self.positions.get(order.symbol, 0)
            return current_position >= order.quantity
    
    def _execute_order(self, order: TradeOrder, price: float):
        """执行订单"""
        if order.side == OrderSide.BUY:
            # 买入
            total_cost = order.quantity * price
            self.cash -= total_cost
            self.positions[order.symbol] = self.positions.get(order.symbol, 0) + order.quantity
        else:  # SELL
            # 卖出
            total_proceeds = order.quantity * price
            self.cash += total_proceeds
            self.positions[order.symbol] = self.positions.get(order.symbol, 0) - order.quantity
        
        order.filled_quantity = order.quantity
        order.filled_price = price


class LiveBroker(BrokerInterface):
    """实盘券商接口"""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str = ""):
        self.logger = TradingLogger(__name__)
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.connected = False
        
    def connect(self) -> bool:
        """连接实盘券商API"""
        self.logger.log_system_event("实盘券商连接", "尝试连接中...")
        
        # 模拟连接过程（实际需要实现具体券商API）
        try:
            # 这里需要根据具体券商实现连接逻辑
            # 例如：Interactive Brokers TWS, Alpaca API等
            self.connected = True
            self.logger.log_system_event("实盘券商连接", "连接成功")
            return True
        except Exception as e:
            self.logger.log_error("连接失败", str(e))
            return False
    
    def disconnect(self) -> bool:
        """断开连接"""
        self.connected = False
        self.logger.log_system_event("实盘券商断开", "断开连接")
        return True
    
    def place_order(self, order: TradeOrder) -> str:
        """下单"""
        if not self.connected:
            raise ConnectionError("Not connected to broker")
        
        # 实盘下单逻辑（需要根据具体券商API实现）
        self.logger.log_trade_execution(
            order.symbol, 
            order.side.value, 
            order.quantity, 
            order.price or 0, 
            "LIVE_ORDER"
        )
        
        # 返回券商生成的订单ID
        return "LIVE_ORDER_ID"
    
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        # 实盘撤单逻辑（需要根据具体券商API实现）
        self.logger.log_system_event("撤单请求", f"订单ID: {order_id}")
        return False  # 默认返回失败，需要具体实现
    
    def get_order_status(self, order_id: str) -> OrderStatus:
        """获取订单状态"""
        # 实盘订单状态查询（需要根据具体券商API实现）
        return OrderStatus.PENDING
    
    def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        # 实盘账户信息查询（需要根据具体券商API实现）
        return {
            'cash': 0.0,
            'total_value': 0.0,
            'buying_power': 0.0
        }
    
    def get_positions(self) -> Dict[str, Any]:
        """获取持仓信息"""
        # 实盘持仓查询（需要根据具体券商API实现）
        return {}


class TradeExecutionEngine:
    """交易执行引擎"""
    
    def __init__(self, broker: BrokerInterface, mode: TradingMode = TradingMode.SIMULATION):
        self.logger = TradingLogger(__name__)
        self.notification_manager = NotificationManager()
        self.broker = broker
        self.mode = mode
        self.db = BacktestDatabase()
        
        # 信号队列
        self.signal_queue = queue.Queue()
        
        # 执行线程
        self.execution_thread = None
        self.is_running = False
        
        # 风险控制参数
        self.max_position_size = 10000  # 单个持仓最大值
        self.max_daily_trades = 50      # 每日最大交易次数
        self.daily_trade_count = 0
        self.last_trade_date = None
        
    def start(self):
        """启动交易执行引擎"""
        if self.is_running:
            return
        
        # 连接券商
        if not self.broker.connect():
            raise ConnectionError("Failed to connect to broker")
        
        self.is_running = True
        self.execution_thread = threading.Thread(target=self._execution_loop)
        self.execution_thread.daemon = True
        self.execution_thread.start()
        
        self.logger.log_system_event("交易引擎启动", f"模式: {self.mode.value}")
        
        # 发送通知
        self.notification_manager.send_notification(
            f"🚀 交易执行引擎已启动\n模式: {self.mode.value}",
            "交易引擎启动"
        )
    
    def stop(self):
        """停止交易执行引擎"""
        self.is_running = False
        if self.execution_thread:
            self.execution_thread.join(timeout=5)
        
        self.broker.disconnect()
        
        self.logger.log_system_event("交易引擎停止", "")
        
        # 发送通知
        self.notification_manager.send_notification(
            "⏹️ 交易执行引擎已停止",
            "交易引擎停止"
        )
    
    def add_signal(self, signal: TradingSignal):
        """添加交易信号"""
        if not self.is_running:
            self.logger.log_error("引擎未运行", "尝试添加信号但引擎未启动")
            return
        
        self.signal_queue.put(signal)
        self.logger.log_strategy_signal(
            signal.symbol, 
            signal.strategy, 
            signal.action, 
            signal.price or 0, 
            signal.reason
        )
    
    def _execution_loop(self):
        """执行循环"""
        while self.is_running:
            try:
                # 获取信号（阻塞1秒）
                signal = self.signal_queue.get(timeout=1)
                
                # 执行信号
                self._execute_signal(signal)
                
            except queue.Empty:
                # 没有信号，继续循环
                continue
            except Exception as e:
                self.logger.log_error("执行异常", str(e))
    
    def _execute_signal(self, signal: TradingSignal):
        """执行交易信号"""
        # 重置每日交易计数
        today = date.today()
        if self.last_trade_date != today:
            self.daily_trade_count = 0
            self.last_trade_date = today
        
        # 风险检查
        if not self._risk_check(signal):
            return
        
        # 创建订单
        order = TradeOrder(
            id="",
            symbol=signal.symbol,
            side=OrderSide.BUY if signal.action.lower() == 'buy' else OrderSide.SELL,
            quantity=signal.quantity,
            order_type=signal.order_type,
            price=signal.price,
            strategy=signal.strategy
        )
        
        try:
            # 下单
            order_id = self.broker.place_order(order)
            
            # 记录交易
            self._record_trade(signal, order_id)
            
            # 更新计数
            self.daily_trade_count += 1
            
            # 发送通知
            self.notification_manager.send_notification(
                f"📈 交易执行\n"
                f"股票: {signal.symbol}\n"
                f"操作: {signal.action}\n"
                f"数量: {signal.quantity}\n"
                f"策略: {signal.strategy}",
                f"交易执行 - {signal.symbol}"
            )
            
        except Exception as e:
            self.logger.log_error("订单执行失败", f"{signal.symbol}: {str(e)}")
    
    def _risk_check(self, signal: TradingSignal) -> bool:
        """风险检查"""
        # 检查每日交易次数
        if self.daily_trade_count >= self.max_daily_trades:
            self.logger.log_risk_event("交易次数超限", signal.symbol, f"今日已执行{self.daily_trade_count}笔交易")
            return False
        
        # 检查持仓大小
        positions = self.broker.get_positions()
        current_value = positions.get(signal.symbol, {}).get('market_value', 0)
        
        if signal.action.lower() == 'buy':
            estimated_price = signal.price or self._estimate_price(signal.symbol)
            new_value = current_value + signal.quantity * estimated_price
            
            if new_value > self.max_position_size:
                self.logger.log_risk_event("持仓超限", signal.symbol, f"持仓将超过{self.max_position_size}")
                return False
        
        # 检查资金
        account_info = self.broker.get_account_info()
        if signal.action.lower() == 'buy':
            estimated_price = signal.price or self._estimate_price(signal.symbol)
            required_cash = signal.quantity * estimated_price
            
            if required_cash > account_info.get('cash', 0):
                self.logger.log_risk_event("资金不足", signal.symbol, f"需要{required_cash}，可用{account_info.get('cash', 0)}")
                return False
        
        return True
    
    def _estimate_price(self, _symbol: str) -> float:
        """估算价格"""
        # 简化实现，实际应该获取实时价格
        return 100.0
    
    def _record_trade(self, signal: TradingSignal, order_id: str):
        """记录交易"""
        # 保存到数据库
        try:
            # 记录交易信息
            self.logger.log_system_event("交易记录", 
                f"订单: {order_id}, 策略: {signal.strategy}, "
                f"股票: {signal.symbol}, 操作: {signal.action}")
        except (ValueError, KeyError) as e:
            self.logger.log_error("记录保存失败", str(e))
    
    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        account_info = self.broker.get_account_info() if self.is_running else {}
        positions = self.broker.get_positions() if self.is_running else {}
        
        return {
            'is_running': self.is_running,
            'mode': self.mode.value,
            'daily_trade_count': self.daily_trade_count,
            'queue_size': self.signal_queue.qsize(),
            'account_info': account_info,
            'positions': positions
        }


# 工厂函数
def create_broker(mode: TradingMode, **kwargs) -> BrokerInterface:
    """创建券商接口"""
    if mode == TradingMode.SIMULATION:
        return SimulationBroker(kwargs.get('initial_cash', 100000.0))
    elif mode == TradingMode.LIVE:
        return LiveBroker(
            kwargs.get('api_key', ''),
            kwargs.get('api_secret', ''),
            kwargs.get('base_url', '')
        )
    else:
        raise ValueError(f"Unsupported trading mode: {mode}")


# 示例用法
if __name__ == "__main__":
    # 创建模拟券商
    broker = create_broker(TradingMode.SIMULATION, initial_cash=100000)
    
    # 创建交易执行引擎
    engine = TradeExecutionEngine(broker, TradingMode.SIMULATION)
    
    try:
        # 启动引擎
        engine.start()
        
        # 创建测试信号
        test_signal = TradingSignal(
            symbol="AAPL",
            strategy="RSI Strategy",
            action="buy",
            quantity=100,
            reason="RSI oversold"
        )
        
        # 添加信号
        engine.add_signal(test_signal)
        
        # 等待执行
        time.sleep(2)
        
        # 获取状态
        status = engine.get_status()
        print(f"Engine Status: {status}")
        
    finally:
        # 停止引擎
        engine.stop()