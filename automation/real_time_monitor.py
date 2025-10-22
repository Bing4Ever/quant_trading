#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 实时数据监控系统 - 实时获取股票价格和交易数据，监控交易信号变化

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import yfinance as yf

from strategies.base_strategy import BaseStrategy
from utils.logger import TradingLogger
from utils.notification import NotificationManager

# 可选的第三方库支持
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

# websocket 支持标志（未来扩展使用）
WEBSOCKET_AVAILABLE = False


@dataclass
class MarketData:
    """市场数据结构"""

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
    """交易信号结构"""

    symbol: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    strength: float  # 信号强度 0-1
    price: float
    timestamp: datetime
    strategy_name: str
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class RealTimeDataProvider:
    """实时数据提供器基类"""

    def __init__(self):
        self.is_connected = False
        self.callbacks = []

    def add_callback(self, callback: Callable[[MarketData], None]):
        """添加数据回调函数"""
        self.callbacks.append(callback)

    def notify_callbacks(self, data: MarketData):
        """通知所有回调函数"""
        for callback in self.callbacks:
            try:
                callback(data)
            except Exception as e:
                logging.error(f"回调函数执行失败: {e}")

    def connect(self) -> bool:
        """连接数据源"""
        raise NotImplementedError

    def disconnect(self):
        """断开连接"""
        raise NotImplementedError

    def subscribe(self, symbols: List[str]):
        """订阅股票数据"""
        raise NotImplementedError


class YFinanceRealTimeProvider(RealTimeDataProvider):
    """基于yfinance的实时数据提供器（轮询模式）"""

    def __init__(self, poll_interval: int = 1):
        super().__init__()
        self.poll_interval = poll_interval
        self.subscribed_symbols = set()
        self.polling_thread = None
        self.stop_polling = threading.Event()
        self.logger = TradingLogger(__name__)

    def connect(self) -> bool:
        """连接数据源"""
        try:
            # 测试连接
            test_data = yf.download("AAPL", period="1d", interval="1m")
            if not test_data.empty:
                self.is_connected = True
                self.logger.log_system_event("yfinance实时数据连接成功")
                return True
        except Exception as e:
            self.logger.log_error("连接失败", f"yfinance连接失败: {e}")
        return False

    def disconnect(self):
        """断开连接"""
        if self.polling_thread and self.polling_thread.is_alive():
            self.stop_polling.set()
            self.polling_thread.join()
        self.is_connected = False
        self.logger.log_system_event("yfinance实时数据连接已断开")

    def subscribe(self, symbols: List[str]):
        """订阅股票数据"""
        self.subscribed_symbols.update(symbols)

        if self.is_connected and not (
            self.polling_thread and self.polling_thread.is_alive()
        ):
            self.stop_polling.clear()
            self.polling_thread = threading.Thread(target=self._polling_loop)
            self.polling_thread.daemon = True
            self.polling_thread.start()
            self.logger.log_system_event("开始监控股票", ', '.join(symbols))

    def _polling_loop(self):
        """轮询循环"""
        while not self.stop_polling.is_set():
            try:
                for symbol in self.subscribed_symbols:
                    data = self._fetch_latest_data(symbol)
                    if data:
                        self.notify_callbacks(data)

                time.sleep(self.poll_interval)
            except Exception as e:
                self.logger.log_error("轮询错误", str(e))
                time.sleep(5)  # 错误后等待5秒

    def _fetch_latest_data(self, symbol: str) -> Optional[MarketData]:
        """获取最新数据"""
        try:
            ticker = yf.Ticker(symbol)

            # 获取最新价格数据
            hist = ticker.history(period="1d", interval="1m")
            if hist.empty:
                return None

            latest = hist.iloc[-1]
            info = ticker.info

            # 计算变化
            if len(hist) > 1:
                prev_close = hist.iloc[-2]["Close"]
                change = latest["Close"] - prev_close
                change_percent = (change / prev_close) * 100
            else:
                change = 0
                change_percent = 0

            return MarketData(
                symbol=symbol,
                price=float(latest["Close"]),
                volume=int(latest["Volume"]),
                timestamp=datetime.now(),
                change=change,
                change_percent=change_percent,
                bid=info.get("bid"),
                ask=info.get("ask"),
            )
        except Exception as e:
            self.logger.log_error("获取数据失败", f"获取{symbol}数据失败: {e}", symbol)
            return None


class AlphaVantageRealTimeProvider(RealTimeDataProvider):
    """Alpha Vantage实时数据提供器"""

    def __init__(self, api_key: str, poll_interval: int = 60):
        super().__init__()
        self.api_key = api_key
        self.poll_interval = poll_interval
        self.subscribed_symbols = set()
        self.polling_thread = None
        self.stop_polling = threading.Event()
        self.logger = TradingLogger(__name__)

    def connect(self) -> bool:
        """连接Alpha Vantage API"""
        if not REQUESTS_AVAILABLE:
            self.logger.log_error("依赖缺失", "requests库未安装，无法使用Alpha Vantage")
            return False

        try:
            # 测试API连接
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={self.api_key}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if "Global Quote" in data:
                    self.is_connected = True
                    self.logger.log_system_event("Alpha Vantage API连接成功")
                    return True
        except Exception as e:
            self.logger.log_error("连接失败", f"Alpha Vantage连接失败: {e}")
        return False

    def subscribe(self, symbols: List[str]):
        """订阅股票数据"""
        self.subscribed_symbols.update(symbols)

        if self.is_connected and not (
            self.polling_thread and self.polling_thread.is_alive()
        ):
            self.stop_polling.clear()
            self.polling_thread = threading.Thread(target=self._polling_loop)
            self.polling_thread.daemon = True
            self.polling_thread.start()
            self.logger.log_system_event("开始监控股票", ', '.join(symbols))

    def _polling_loop(self):
        """轮询循环"""
        while not self.stop_polling.is_set():
            try:
                for symbol in self.subscribed_symbols:
                    data = self._fetch_alpha_vantage_data(symbol)
                    if data:
                        self.notify_callbacks(data)
                    time.sleep(12)  # Alpha Vantage API限制：每分钟5次调用

                time.sleep(self.poll_interval)
            except Exception as e:
                self.logger.log_error("轮询错误", f"Alpha Vantage轮询错误: {e}")
                time.sleep(60)

    def _fetch_alpha_vantage_data(self, symbol: str) -> Optional[MarketData]:
        """从Alpha Vantage获取数据"""
        if not REQUESTS_AVAILABLE:
            return None

        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.api_key}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                quote = data.get("Global Quote", {})

                if quote:
                    return MarketData(
                        symbol=symbol,
                        price=float(quote.get("05. price", 0)),
                        volume=int(quote.get("06. volume", 0)),
                        timestamp=datetime.now(),
                        change=float(quote.get("09. change", 0)),
                        change_percent=float(
                            quote.get("10. change percent", "0%").rstrip("%")
                        ),
                    )
        except Exception as e:
            self.logger.log_error("获取数据失败", f"Alpha Vantage获取{symbol}数据失败: {e}", symbol)
        return None

    def disconnect(self):
        """断开连接"""
        if self.polling_thread and self.polling_thread.is_alive():
            self.stop_polling.set()
            self.polling_thread.join()
        self.is_connected = False
        self.logger.log_system_event("Alpha Vantage连接已断开")


class SignalMonitor:
    """交易信号监控器"""

    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
        self.signal_history: List[TradingSignal] = []
        self.signal_callbacks: List[Callable[[TradingSignal], None]] = []
        self.logger = TradingLogger(__name__)
        self.lock = threading.Lock()

    def add_strategy(self, name: str, strategy: BaseStrategy):
        """添加监控策略"""
        self.strategies[name] = strategy
        self.logger.log_system_event("添加策略监控", name)

    def remove_strategy(self, name: str):
        """移除监控策略"""
        if name in self.strategies:
            del self.strategies[name]
            self.logger.log_system_event("移除策略监控", name)

    def add_signal_callback(self, callback: Callable[[TradingSignal], None]):
        """添加信号回调函数"""
        self.signal_callbacks.append(callback)

    def process_market_data(self, market_data: MarketData):
        """处理市场数据并生成信号"""
        with self.lock:
            try:
                # 为每个策略生成信号
                for strategy_name, _ in self.strategies.items():
                    signal = self._generate_signal(strategy_name, market_data)
                    if signal:
                        self._handle_new_signal(signal)
            except Exception as e:
                self.logger.log_error("处理数据失败", f"处理市场数据失败: {e}")

    def _generate_signal(
        self, strategy_name: str, market_data: MarketData
    ) -> Optional[TradingSignal]:
        """为单个策略生成信号"""
        try:
            # 实现基于市场数据的信号生成逻辑
            symbol = market_data.symbol
            price = market_data.price

            # 基于价格变化生成信号
            if market_data.change_percent:
                if market_data.change_percent > 2:
                    signal_type = "BUY"
                    strength = min(market_data.change_percent / 10, 1.0)
                elif market_data.change_percent < -2:
                    signal_type = "SELL"
                    strength = min(abs(market_data.change_percent) / 10, 1.0)
                else:
                    signal_type = "HOLD"
                    strength = 0.1

                return TradingSignal(
                    symbol=symbol,
                    signal_type=signal_type,
                    strength=strength,
                    price=price,
                    timestamp=market_data.timestamp,
                    strategy_name=strategy_name,
                    confidence=strength,
                    metadata={
                        "change_percent": market_data.change_percent,
                        "volume": market_data.volume,
                    },
                )
        except Exception as e:
            self.logger.log_error("信号生成失败", f"策略{strategy_name}信号生成失败: {e}")
        return None

    def _handle_new_signal(self, signal: TradingSignal):
        """处理新信号"""
        # 保存到历史记录
        self.signal_history.append(signal)

        # 限制历史记录长度
        if len(self.signal_history) > 1000:
            self.signal_history = self.signal_history[-1000:]

        # 通知回调函数
        for callback in self.signal_callbacks:
            try:
                callback(signal)
            except Exception as e:
                self.logger.log_error("回调执行失败", f"信号回调函数执行失败: {e}")

        # 记录信号
        self.logger.log_strategy_signal(
            signal.symbol, signal.strategy_name, signal.signal_type,
            signal.price, f"强度:{signal.strength:.2f}"
        )

    def get_latest_signals(
        self, symbol: str = None, limit: int = 10
    ) -> List[TradingSignal]:
        """获取最新信号"""
        with self.lock:
            signals = self.signal_history
            if symbol:
                signals = [s for s in signals if s.symbol == symbol]
            return signals[-limit:]


class RealTimeMonitor:
    """实时监控系统主类"""

    def __init__(self, data_provider: RealTimeDataProvider):
        self.data_provider = data_provider
        self.signal_monitor = SignalMonitor()
        self.notification_manager = NotificationManager()
        self.logger = TradingLogger(__name__)

        self.is_running = False
        self.monitored_symbols = set()

        # 连接数据提供器和信号监控器
        self.data_provider.add_callback(self.signal_monitor.process_market_data)
        self.signal_monitor.add_signal_callback(self._handle_trading_signal)

    def start_monitoring(
        self, monitor_symbols: List[str], strategies: Dict[str, BaseStrategy] = None
    ):
        """开始实时监控"""
        try:
            # 连接数据源
            if not self.data_provider.connect():
                raise ConnectionError("数据源连接失败")

            # 添加策略
            if strategies:
                for name, strategy in strategies.items():
                    self.signal_monitor.add_strategy(name, strategy)

            # 订阅股票数据
            self.data_provider.subscribe(monitor_symbols)
            self.monitored_symbols.update(monitor_symbols)

            self.is_running = True
            self.logger.log_system_event("开始实时监控", ', '.join(monitor_symbols))

            # 发送通知
            self.notification_manager.send_notification(
                f"📊 实时监控已启动\n监控股票: {', '.join(monitor_symbols)}", "实时监控启动"
            )

        except Exception as e:
            self.logger.log_error("启动失败", f"启动监控失败: {e}")
            raise

    def stop_monitoring(self):
        """停止实时监控"""
        if self.is_running:
            self.data_provider.disconnect()
            self.is_running = False
            self.logger.log_system_event("实时监控已停止")

            # 发送通知
            self.notification_manager.send_notification(
                "📊 实时监控已停止", "实时监控停止"
            )

    def add_symbol(self, symbol: str):
        """添加监控股票"""
        if symbol not in self.monitored_symbols:
            self.data_provider.subscribe([symbol])
            self.monitored_symbols.add(symbol)
            self.logger.log_system_event("添加监控股票", symbol)

    def remove_symbol(self, symbol: str):
        """移除监控股票"""
        if symbol in self.monitored_symbols:
            self.monitored_symbols.remove(symbol)
            self.logger.log_system_event("移除监控股票", symbol)
            # 注意：这里需要实现数据提供器的取消订阅功能

    def _handle_trading_signal(self, signal: TradingSignal):
        """处理交易信号"""
        # 过滤重要信号
        if signal.signal_type in ["BUY", "SELL"] and signal.strength > 0.7:
            message = (
                f"🚨 交易信号\n"
                f"股票: {signal.symbol}\n"
                f"信号: {signal.signal_type}\n"
                f"强度: {signal.strength:.2f}\n"
                f"价格: ${signal.price:.2f}\n"
                f"策略: {signal.strategy_name}\n"
                f"时间: {signal.timestamp.strftime('%H:%M:%S')}"
            )

            self.notification_manager.send_notification(
                message, f"交易信号 - {signal.symbol}"
            )

    def get_monitoring_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        return {
            "is_running": self.is_running,
            "is_connected": self.data_provider.is_connected,
            "monitored_symbols": list(self.monitored_symbols),
            "active_strategies": list(self.signal_monitor.strategies.keys()),
            "recent_signals_count": len(self.signal_monitor.signal_history[-10:]),
        }

    def get_market_summary(self) -> Dict[str, Any]:
        """获取市场摘要"""
        recent_signals = self.signal_monitor.get_latest_signals(limit=50)

        # 统计信号分布
        signal_counts = {}
        for signal in recent_signals:
            signal_counts[signal.signal_type] = (
                signal_counts.get(signal.signal_type, 0) + 1
            )

        # 活跃股票
        active_symbols = list({signal.symbol for signal in recent_signals[-20:]})

        return {
            "total_signals_today": len(recent_signals),
            "signal_distribution": signal_counts,
            "active_symbols": active_symbols,
            "last_update": datetime.now().strftime("%H:%M:%S"),
        }


# 示例使用
if __name__ == "__main__":
    # 创建实时监控系统
    provider = YFinanceRealTimeProvider(poll_interval=5)
    rt_monitor = RealTimeMonitor(provider)

    # 开始监控
    test_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]

    try:
        rt_monitor.start_monitoring(test_symbols)

        # 运行一段时间
        time.sleep(60)

    except KeyboardInterrupt:
        print("停止监控...")
    finally:
        rt_monitor.stop_monitoring()
