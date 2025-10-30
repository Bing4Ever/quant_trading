#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulation Trading Environment
完整的模拟交易环境，集成所有系统组件进行端到端测试
"""

import time
import threading
import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

import numpy as np

from src.tradingagent.modules.strategies import MultiStrategyRunner
from src.tradingagent import (
    TradingSignal,
    TradingMode,
    Order,
    OrderSide,
    IBroker,
)
from src.tradingagent.core.brokers import BrokerFactory
from src.tradingagent.modules.risk_management import RiskManager, PositionLimits
from src.common.logger import TradingLogger
from src.common.notification import NotificationManager
from src.tradingservice.services.automation import RealTimeMonitor, ReportGenerator
from src.tradingservice.services.orchestration import TaskManager
from src.tradingservice.dataaccess import get_backtest_repository
from config import config as app_config


class SimulationMode(Enum):
    """模拟模式"""
    BACKTESTING = "backtesting"      # 历史数据回测
    LIVE_SIM = "live_simulation"     # 实时模拟
    PAPER_TRADING = "paper_trading"  # 纸上交易


class _FallbackPriceFeed:
    """基础价格源，用于在缺少实时行情时提供估值。"""

    def __init__(self, default_price: float = 100.0):
        self._prices: Dict[str, float] = {}
        self._default_price = default_price

    def get_current_price(self, symbol: str) -> float:
        """返回指定标的的最新价格，若无记录则生成默认值。"""
        if symbol not in self._prices:
            self._prices[symbol] = self._default_price
        return self._prices[symbol]

    def update_price(self, symbol: str, price: Optional[float]) -> float:
        """根据传入线索刷新价格缓存，并返回最新价格。"""
        if price is not None and price > 0:
            self._prices[symbol] = price
        return self.get_current_price(symbol)


class _DummyDataProvider:
    """模拟实时数据源，满足实时监控组件的接口需求。"""

    def __init__(self, update_interval: float = 1.0):
        self._callbacks: List[Any] = []
        self._subscribed_symbols: set[str] = set()
        self._prices: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._active = False
        self._thread: Optional[threading.Thread] = None
        self._update_interval = update_interval
        self._price_feed: Optional[_FallbackPriceFeed] = None

    def add_callback(self, callback) -> None:
        """登记数据推送回调。"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def set_price_feed(self, price_feed: _FallbackPriceFeed) -> None:
        """注入基础价格源，保持价格缓存同步。"""
        self._price_feed = price_feed

    def connect(self) -> bool:
        """模拟连接过程，同时启动价格推送循环。"""
        if self._active:
            return True
        self._active = True
        self._ensure_loop()
        return True

    def disconnect(self) -> bool:
        """模拟断开过程，并停止价格推送。"""
        if not self._active:
            return True
        self._active = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        return True

    def subscribe(self, symbols: List[str]) -> None:
        """注册需要推送行情的标的。"""
        with self._lock:
            for symbol in symbols:
                if symbol not in self._subscribed_symbols:
                    self._subscribed_symbols.add(symbol)
                    initial_price = self._get_price(symbol)
                    self._prices[symbol] = initial_price
                    self._broadcast(symbol, initial_price)

    def publish_price(self, symbol: str, price: float) -> None:
        """向已注册的回调广播行情数据。"""
        recorded_price = self._record_price(symbol, price)
        self._broadcast(symbol, recorded_price)

    def _ensure_loop(self) -> None:
        """确保行情推送线程处于运行状态。"""
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._run_price_loop,
            name="DummyMarketDataFeed",
            daemon=True,
        )
        self._thread.start()

    def _run_price_loop(self) -> None:
        """定期生成随机行情变动并推送。"""
        while self._active:
            with self._lock:
                symbols = list(self._subscribed_symbols)

            for symbol in symbols:
                base_price = self._get_price(symbol)
                random_change = random.uniform(-0.002, 0.002)
                new_price = max(base_price * (1 + random_change), 0.01)
                recorded_price = self._record_price(symbol, new_price)
                self._broadcast(symbol, recorded_price)

            time.sleep(self._update_interval)

    def _get_price(self, symbol: str) -> float:
        """获取当前记账价格（优先读取共享缓存）。"""
        if self._price_feed is not None:
            return self._price_feed.get_current_price(symbol)
        return self._prices.get(symbol, 100.0)

    def _record_price(self, symbol: str, price: float) -> float:
        """更新基础价格源与本地缓存，保持模拟行情一致。"""
        if self._price_feed is not None:
            recorded = self._price_feed.update_price(symbol, price)
        else:
            recorded = price
        with self._lock:
            self._prices[symbol] = recorded
        return recorded

    def _broadcast(self, symbol: str, price: float) -> None:
        """广播生成的行情快照。"""
        payload = {
            "symbol": symbol,
            "price": price,
            "timestamp": datetime.now().isoformat(),
        }
        for callback in list(self._callbacks):
            try:
                callback(payload)
            except Exception:
                continue


class TradeExecutionEngine:
    """模拟交易执行器，负责将信号转化为订单并更新账户状态。"""

    def __init__(
        self,
        broker: IBroker,
        mode: TradingMode = TradingMode.SIMULATION,
        market_data_provider: Optional[_DummyDataProvider] = None,
    ):
        self.broker = broker
        self.mode = mode
        self.logger = TradingLogger(f"{__name__}.TradeExecutionEngine")
        self.active = False
        self.price_feed = _FallbackPriceFeed()
        self.trade_log: List[Dict[str, Any]] = []
        self.market_data_provider = market_data_provider

        # 将内部价格源注入模拟券商，弥补缺失的数据提供者。
        self.broker.data_provider = self.price_feed

    def start(self) -> None:
        """启动执行引擎并建立券商连接。"""
        if self.active:
            return
        self.broker.connect()
        self.active = True
        self.logger.log_system_event("Trade execution engine started", self.mode.value)

    def stop(self) -> None:
        """停止执行引擎并断开券商连接。"""
        if not self.active:
            return
        self.broker.disconnect()
        self.active = False
        self.logger.log_system_event("Trade execution engine stopped", self.mode.value)

    def submit_signal(self, signal: TradingSignal) -> bool:
        """接收交易信号并尝试生成订单。"""
        if not self.active:
            self.logger.warning("Trade engine is inactive, signal discarded")
            return False

        quantity = int(max(signal.quantity, 0))
        if quantity == 0:
            self.logger.warning("Signal quantity is zero, skip execution")
            return False

        side = OrderSide.BUY if signal.action.lower() == "buy" else OrderSide.SELL
        reference_price = self.price_feed.update_price(signal.symbol, signal.price)

        # 记录卖出前的平均持仓成本，用于估算盈亏。
        pre_trade_avg_cost = self._get_average_cost(signal.symbol)

        order = Order(
            order_id=str(uuid.uuid4()),
            symbol=signal.symbol,
            side=side,
            quantity=quantity,
            order_type=signal.order_type,
            price=reference_price,
            strategy=signal.strategy,
        )

        submitted = self.broker.submit_order(order)
        if not submitted:
            self.logger.warning("Signal rejected by broker: %s %s", signal.symbol, signal.action)
            return False

        filled_price = order.filled_price or reference_price
        self.price_feed.update_price(signal.symbol, filled_price)
        if self.market_data_provider:
            self.market_data_provider.publish_price(signal.symbol, filled_price)

        trade_entry = {
            "timestamp": order.timestamp,
            "symbol": order.symbol,
            "side": order.side.value,
            "quantity": order.quantity,
            "price": filled_price,
            "order_id": order.order_id,
            "strategy": order.strategy,
            "pnl": 0.0,
        }

        if side == OrderSide.SELL and pre_trade_avg_cost is not None:
            trade_entry["pnl"] = (filled_price - pre_trade_avg_cost) * order.quantity

        self.trade_log.append(trade_entry)
        return True

    def get_portfolio_value(self) -> float:
        """返回账户总资产估值。"""
        balance = self.broker.get_account_balance()
        return balance.get("equity", balance.get("cash", 0.0))

    def get_available_cash(self) -> float:
        """返回可用现金。"""
        balance = self.broker.get_account_balance()
        return balance.get("cash", 0.0)

    def get_all_positions(self) -> Dict[str, int]:
        """返回当前全部持仓数量。"""
        positions = self.broker.get_positions()
        return {pos.symbol: pos.quantity for pos in positions}

    def get_position(self, symbol: str) -> int:
        """查询指定标的持仓数量。"""
        return self.get_all_positions().get(symbol, 0)

    def get_trade_history(self) -> List[Dict[str, Any]]:
        """返回简化交易记录，时间字段转换为 ISO 格式。"""
        history = []
        for record in self.trade_log:
            normalized = dict(record)
            timestamp = normalized.get("timestamp")
            if isinstance(timestamp, datetime):
                normalized["timestamp"] = timestamp.isoformat()
            history.append(normalized)
        return history

    def _get_average_cost(self, symbol: str) -> Optional[float]:
        """读取券商记录的平均持仓成本。"""
        position = self.broker.positions.get(symbol) if hasattr(self.broker, "positions") else None
        if position:
            return position.get("average_price")
        return None


@dataclass
class SimulationConfig:
    """模拟配置"""
    mode: SimulationMode = SimulationMode.LIVE_SIM
    initial_capital: float = 100000.0
    broker_id: Optional[str] = None
    symbols: Optional[List[str]] = None
    strategies: Optional[List[str]] = None
    duration_hours: int = 24
    data_period: str = "1y"
    data_interval: str = "1d"
    risk_enabled: bool = True
    notifications_enabled: bool = True
    reports_enabled: bool = True

    def __post_init__(self):
        if not self.broker_id:
            self.broker_id = app_config.get('brokers.default', 'simulation')
        if self.symbols is None:
            self.symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        if self.strategies is None:
            self.strategies = ["all"]


class SimulationEnvironment:
    """模拟交易环境"""

    def __init__(self, config: SimulationConfig = None):
        """
        初始化模拟环境

        Args:
            config: 模拟配置
        """
        self.config = config or SimulationConfig()
        self.logger = TradingLogger(__name__)

        # 系统组件初始化
        self._initialize_components()

        # 模拟状态
        self.is_running = False
        self.start_time = None
        self.simulation_thread = None

        # 性能跟踪
        self.performance_metrics = {
            'trades_executed': 0,
            'signals_generated': 0,
            'risk_alerts': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'sharpe_ratio': 0.0
        }

        self.logger.log_system_event("Simulation environment initialized", f"Mode: {self.config.mode.value}")

    def _initialize_components(self):
        """初始化系统组件"""
        # 策略运行器
        self.strategy_runner = MultiStrategyRunner()

        # 风险管理
        if self.config.risk_enabled:
            risk_limits = PositionLimits()
            risk_limits.max_position_value = self.config.initial_capital * 0.2  # 20% max position
            risk_limits.max_portfolio_concentration = 0.25  # 25% max concentration
            risk_limits.max_total_exposure = 0.8  # 80% max exposure
            risk_limits.max_daily_loss = 0.05  # 5% daily loss limit

            self.risk_manager = RiskManager(limits=risk_limits)
        else:
            self.risk_manager = None

        # 基础行情数据源
        self.market_data_provider = _DummyDataProvider()

        # 交易执行引擎
        broker_type, broker_params = app_config.resolve_broker(self.config.broker_id)
        if broker_type == "simulation":
            broker_params.setdefault("initial_capital", self.config.initial_capital)
            broker_params.setdefault("data_provider", self.market_data_provider)

        broker_instance = BrokerFactory.create(broker_type, **broker_params)

        self.execution_engine = TradeExecutionEngine(
            broker=broker_instance,
            mode=TradingMode.SIMULATION,
            market_data_provider=self.market_data_provider
        )
        # 共享价格缓存，确保模拟行情与执行引擎一致
        self.market_data_provider.set_price_feed(self.execution_engine.price_feed)

        # 通知管理器
        if self.config.notifications_enabled:
            self.notification_manager = NotificationManager()
        else:
            self.notification_manager = None

        # 任务管理器，串联实时信号到 TaskManager -> OrderExecutor 链路
        self.task_manager = TaskManager(broker=self.execution_engine.broker)

        # 实时监控器
        self.real_time_monitor = RealTimeMonitor(
            data_provider=self.market_data_provider,
            task_manager=self.task_manager,
        )

        # 报告生成器
        if self.config.reports_enabled:
            self.report_generator = ReportGenerator()
        else:
            self.report_generator = None

        # 数据存储
        self.trade_history = []
        self.signal_history = []
        self.portfolio_history = []

        self.logger.log_system_event("All system components initialized successfully", "")

    def start_simulation(self):
        """启动模拟交易"""
        if self.is_running:
            self.logger.warning("Simulation is already running")
            return False

        try:
            self.is_running = True
            self.start_time = datetime.now()

            # 启动风险管理
            if self.risk_manager:
                self.risk_manager.start()

            # 启动交易执行引擎
            self.execution_engine.start()

            # 启动实时监控
            if hasattr(self.real_time_monitor, "start_monitoring"):
                self.real_time_monitor.start_monitoring(self.config.symbols)
            elif hasattr(self.real_time_monitor, "start"):
                self.real_time_monitor.start()

            # 启动模拟主循环
            self.simulation_thread = threading.Thread(
                target=self._simulation_loop,
                name="SimulationThread"
            )
            self.simulation_thread.daemon = True
            self.simulation_thread.start()

            # 发送启动通知
            if self.notification_manager:
                self.notification_manager.send_notification(
                    f"🚀 Simulation Started\n"
                    f"Mode: {self.config.mode.value}\n"
                    f"Symbols: {', '.join(self.config.symbols)}\n"
                    f"Initial Capital: ${self.config.initial_capital:,.2f}\n"
                    f"Duration: {self.config.duration_hours} hours",
                    "Trading Simulation Started"
                )

            self.logger.log_system_event("Simulation started successfully", f"Mode: {self.config.mode.value}")
            return True

        except ValueError as e:
            self.logger.error(f"Value error occurred: {str(e)}")
            return False
        except KeyError as e:
            self.logger.error(f"Key error occurred: {str(e)}")
            return False
        except Exception as e:
            self.logger.log_error("Simulation Start", f"Failed to start simulation: {str(e)}")
            self.is_running = False
            return False

    def stop_simulation(self):
        """停止模拟交易"""
        if not self.is_running:
            self.logger.warning("Simulation is not running")
            return

        try:
            self.is_running = False

            # 停止各系统组件
            if self.risk_manager:
                self.risk_manager.stop()

            self.execution_engine.stop()
            if hasattr(self.real_time_monitor, "stop_monitoring"):
                self.real_time_monitor.stop_monitoring()
            elif hasattr(self.real_time_monitor, "stop"):
                self.real_time_monitor.stop()

            # 生成最终报告
            self._generate_final_report()

            # 发送停止通知
            if self.notification_manager:
                self.notification_manager.send_notification(
                    f"🏁 Simulation Completed\n"
                    f"Duration: {self._get_simulation_duration()}\n"
                    f"Trades: {self.performance_metrics['trades_executed']}\n"
                    f"Total P&L: ${self.performance_metrics['total_pnl']:,.2f}\n"
                    f"Win Rate: {self.performance_metrics['win_rate']:.1%}",
                    "Trading Simulation Completed"
                )

            self.logger.log_system_event("Simulation stopped successfully", "")

        except Exception as e:
            self.logger.log_error("Simulation Stop", f"Error stopping simulation: {str(e)}")

    def _simulation_loop(self):
        """模拟交易主循环"""
        end_time = self.start_time + timedelta(hours=self.config.duration_hours)

        while self.is_running and datetime.now() < end_time:
            try:
                # 运行策略分析
                self._run_strategy_analysis()

                # 更新投资组合数据
                self._update_portfolio_tracking()

                # 检查风险指标
                if self.risk_manager:
                    self._check_risk_status()

                # 睡眠间隔
                time.sleep(60)  # 1分钟间隔

            except Exception as e:
                self.logger.log_error("Simulation Loop", f"Error in simulation loop: {str(e)}")
                time.sleep(5)

        # 自然结束
        if self.is_running:
            self.stop_simulation()

    def _run_strategy_analysis(self):
        """运行策略分析"""
        try:
            for symbol in self.config.symbols:
                # 运行策略分析
                results = self.strategy_runner.run_all_strategies(
                    symbol=symbol,
                    period=self.config.data_period,
                    selected_strategies=None if self.config.strategies == ["all"] else self.config.strategies,
                    interval=self.config.data_interval,
                )

                if results:
                    # 分析结果并生成交易信号
                    signals = self._analyze_results_for_signals(symbol, results)

                    for signal in signals:
                        # 记录信号
                        self.signal_history.append({
                            'timestamp': datetime.now(),
                            'symbol': symbol,
                            'signal': signal,
                            'strategy_results': results
                        })

                        # 提交到执行引擎
                        success = self.execution_engine.submit_signal(signal)

                        if success:
                            self.performance_metrics['signals_generated'] += 1
                            signal_info = f"{signal.symbol} {signal.action} {signal.quantity}"
                            self.logger.log_system_event("Signal submitted", signal_info)

        except Exception as e:
            self.logger.log_error("Strategy Analysis", f"Error in strategy analysis: {str(e)}")

    def _analyze_results_for_signals(self, symbol: str, results: Dict) -> List[TradingSignal]:  # pylint: disable=unused-argument
        """分析策略结果生成交易信号"""
        signals = []

        try:
            # 获取比较报告
            comparison_df = self.strategy_runner.generate_comparison_report()

            if not comparison_df.empty:
                # 取最佳策略的建议
                best_strategy = comparison_df.iloc[0]

                # 根据夏普比率和收益率决定信号强度
                sharpe_ratio = best_strategy.get('夏普比率', 0)
                total_return = best_strategy.get('总收益率', 0)

                if sharpe_ratio > 1.5 and total_return > 0.1:  # 强买入信号
                    quantity = int(self.config.initial_capital * 0.1 / 150)  # 假设价格150

                    signal = TradingSignal(
                        symbol=symbol,
                        strategy=best_strategy.get('策略名称', 'unknown'),
                        action='buy',
                        quantity=quantity,
                        price=None,  # 市价
                        confidence=min(sharpe_ratio / 2.0, 1.0),
                        reason=f"Strong buy signal: Sharpe={sharpe_ratio:.2f}, Return={total_return:.2%}",
                        timestamp=datetime.now()
                    )
                    signals.append(signal)

                elif sharpe_ratio < 0.5 and total_return < -0.05:  # 卖出信号
                    # 检查是否有持仓
                    current_position = self.execution_engine.get_position(symbol)
                    if current_position and current_position > 0:
                        signal = TradingSignal(
                            symbol=symbol,
                            strategy=best_strategy.get('策略名称', 'unknown'),
                            action='sell',
                            quantity=current_position // 2,  # 卖出一半
                            price=None,
                            confidence=abs(sharpe_ratio - 0.5),
                            reason=f"Sell signal: Sharpe={sharpe_ratio:.2f}, Return={total_return:.2%}",
                            timestamp=datetime.now()
                        )
                        signals.append(signal)

        except Exception as e:
            self.logger.log_error("Signal Analysis", f"Error analyzing results for {symbol}: {str(e)}", symbol)

        return signals

    def _update_portfolio_tracking(self):
        """更新投资组合跟踪"""
        try:
            # 获取当前投资组合状态
            portfolio_value = self.execution_engine.get_portfolio_value()
            positions = self.execution_engine.get_all_positions()

            # 记录历史
            self.portfolio_history.append({
                'timestamp': datetime.now(),
                'portfolio_value': portfolio_value,
                'positions': positions.copy(),
                'cash': self.execution_engine.get_available_cash()
            })

            # 更新风险管理器
            if self.risk_manager:
                # 转换持仓格式
                position_values = {}
                for symbol, quantity in positions.items():
                    # 这里应该获取实际价格，暂时使用固定价格
                    estimated_price = 150.0  # 简化处理
                    position_values[symbol] = quantity * estimated_price

                self.risk_manager.update_portfolio(portfolio_value, position_values)

            # 计算性能指标
            self._calculate_performance_metrics()

        except Exception as e:
            self.logger.error(f"Error updating portfolio tracking: {str(e)}")

    def _check_risk_status(self):
        """检查风险状态"""
        try:
            if not self.risk_manager:
                return

            # 风险管理器会自动监控并发送警报

        except Exception as e:
            self.logger.error(f"Error checking risk status: {str(e)}")

    def _calculate_performance_metrics(self):
        """计算性能指标"""
        try:
            if len(self.portfolio_history) < 2:
                return

            # 计算总收益
            initial_value = self.config.initial_capital
            current_value = self.portfolio_history[-1]['portfolio_value']
            self.performance_metrics['total_pnl'] = current_value - initial_value

            # 计算收益率序列
            returns = []
            for i in range(1, len(self.portfolio_history)):
                prev_value = self.portfolio_history[i-1]['portfolio_value']
                curr_value = self.portfolio_history[i]['portfolio_value']
                if prev_value > 0:
                    returns.append((curr_value - prev_value) / prev_value)

            if returns:
                returns_array = np.array(returns)

                # 计算夏普比率
                if len(returns) > 1:
                    mean_return = np.mean(returns_array)
                    std_return = np.std(returns_array)
                    if std_return > 0:
                        self.performance_metrics['sharpe_ratio'] = mean_return / std_return * np.sqrt(252)  # 年化

            # 计算胜率
            trades = self.execution_engine.get_trade_history()
            if trades:
                profitable_trades = sum(1 for trade in trades if trade.get('pnl', 0) > 0)
                self.performance_metrics['win_rate'] = profitable_trades / len(trades)
                self.performance_metrics['trades_executed'] = len(trades)

        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {str(e)}")

    def _generate_final_report(self) -> str:
        """生成最终报告"""
        try:
            if not self.report_generator:
                return ""

            # 收集报告数据
            report_data = {
                'simulation_config': {
                    'mode': self.config.mode.value,
                    'duration_hours': self.config.duration_hours,
                    'symbols': self.config.symbols,
                    'initial_capital': self.config.initial_capital
                },
                'performance_metrics': self.performance_metrics,
                'portfolio_history': self.portfolio_history[-10:],  # 最近10个记录
                'signal_history': self.signal_history[-20:],  # 最近20个信号
                'trade_history': self.execution_engine.get_trade_history()
            }

            # 生成报告
            report_file = self.report_generator.generate_simulation_report(report_data)
            self.logger.log_system_event("Simulation report generated", report_file)

            return report_file

        except Exception as e:
            self.logger.error(f"Error generating final report: {str(e)}")
            return ""

    def _get_simulation_duration(self) -> str:
        """获取模拟运行时间"""
        if not self.start_time:
            return "Unknown"

        duration = datetime.now() - self.start_time
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        return f"{duration.days}d {hours}h {minutes}m"

    def get_status(self) -> Dict[str, Any]:
        """获取模拟状态"""
        portfolio_value = (self.portfolio_history[-1]['portfolio_value']
                           if self.portfolio_history
                           else self.config.initial_capital)

        return {
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'duration': self._get_simulation_duration(),
            'performance_metrics': self.performance_metrics,
            'portfolio_value': portfolio_value,
            'signals_count': len(self.signal_history),
            'trades_count': self.performance_metrics['trades_executed']
        }

    def add_manual_signal(self, symbol: str, action: str, quantity: int) -> bool:
        """手动添加交易信号"""
        try:
            signal = TradingSignal(
                symbol=symbol,
                strategy='manual',
                action=action,
                quantity=quantity,
                price=None,
                confidence=1.0,
                reason="Manual signal from user",
                timestamp=datetime.now()
            )

            success = self.execution_engine.submit_signal(signal)

            if success:
                self.signal_history.append({
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'signal': signal,
                    'strategy_results': {'manual': True}
                })

                self.logger.log_system_event("Manual signal submitted", f"{symbol} {action} {quantity}")

            return success

        except Exception as e:
            self.logger.error(f"Error submitting manual signal: {str(e)}")
            return False


def main():
    """模拟环境使用示例"""
    print("=" * 60)
    print("QUANTITATIVE TRADING SIMULATION ENVIRONMENT")
    print("=" * 60)

    # 创建模拟配置
    config = SimulationConfig(
        mode=SimulationMode.LIVE_SIM,
        initial_capital=50000.0,
        symbols=["AAPL", "MSFT", "TSLA"],
        duration_hours=2,  # 2小时模拟
        risk_enabled=True,
        notifications_enabled=False,  # 关闭通知避免干扰
        reports_enabled=True
    )

    # 创建模拟环境
    sim_env = SimulationEnvironment(config)

    try:
        print("\n🚀 Starting simulation...")
        print(f"Mode: {config.mode.value}")
        print(f"Symbols: {', '.join(config.symbols)}")
        print(f"Initial Capital: ${config.initial_capital:,.2f}")
        print(f"Duration: {config.duration_hours} hours")

        # 启动模拟
        success = sim_env.start_simulation()

        if success:
            print("✅ Simulation started successfully!")
            print("Press Ctrl+C to stop simulation early...")

            # 监控运行状态
            while sim_env.is_running:
                time.sleep(30)  # 每30秒检查一次

                status = sim_env.get_status()
                print("\n📊 Status Update:")
                print(f"   Duration: {status['duration']}")
                print(f"   Portfolio Value: ${status['portfolio_value']:,.2f}")
                print(f"   Signals Generated: {status['signals_count']}")
                print(f"   Trades Executed: {status['trades_count']}")
                pnl = sim_env.performance_metrics['total_pnl']
                print(f"   Total P&L: ${pnl:,.2f}")

            print("\n🏁 Simulation completed!")

        else:
            print("❌ Failed to start simulation")

    except KeyboardInterrupt:
        print("\n🛑 Simulation stopped by user")
        sim_env.stop_simulation()

    except Exception as e:
        print(f"❌ Simulation error: {str(e)}")
        sim_env.stop_simulation()

    # 显示最终结果
    final_status = sim_env.get_status()
    print("\n" + "=" * 60)
    print("FINAL SIMULATION RESULTS")
    print("=" * 60)
    print(f"Total Duration: {final_status['duration']}")
    print(f"Final Portfolio Value: ${final_status['portfolio_value']:,.2f}")
    print(f"Total P&L: ${sim_env.performance_metrics['total_pnl']:,.2f}")
    return_pct = (sim_env.performance_metrics['total_pnl'] / config.initial_capital) * 100
    print(f"Return: {return_pct:.2f}%")
    print(f"Trades Executed: {sim_env.performance_metrics['trades_executed']}")
    print(f"Win Rate: {sim_env.performance_metrics['win_rate']:.1%}")
    print(f"Sharpe Ratio: {sim_env.performance_metrics['sharpe_ratio']:.2f}")


if __name__ == "__main__":
    main()
