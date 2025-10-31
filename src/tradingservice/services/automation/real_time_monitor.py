#!/usr/bin/env python3
"""
实时行情监控协调器。

该模块仅负责将数据提供器与信号监控器组合成高层接口，具体数据抓取与信号计算
逻辑分别拆分在 ``realtime_provider`` 与 ``signal_monitor`` 模块中。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from src.common.logger import TradingLogger
from src.common.notification import NotificationManager
from src.tradingagent.modules.strategies import BaseStrategy

from .automation_models import MarketData, TradingSignal
from .realtime_provider import RealTimeDataProvider, PollingDataProvider
from .signal_monitor import SignalMonitor

__all__ = ["RealTimeMonitor", "SignalMonitor", "RealTimeDataProvider", "PollingDataProvider"]

if TYPE_CHECKING:
    from src.tradingservice.services.orchestration import TaskManager



class RealTimeMonitor:
    """协调数据提供器与信号监控器的高层组件。"""

    def __init__(
        self,
        data_provider: Optional[RealTimeDataProvider] = None,
        *,
        task_manager: Optional["TaskManager"] = None,
    ) -> None:
        self.data_provider = data_provider or PollingDataProvider()
        monitor_kwargs: Dict[str, Any] = {}
        if isinstance(self.data_provider, PollingDataProvider):
            underlying = getattr(self.data_provider, "data_provider", None)
            if underlying is not None:
                monitor_kwargs["data_provider"] = underlying
        self.signal_monitor = SignalMonitor(**monitor_kwargs)
        self.notification_manager = NotificationManager()
        self.logger = TradingLogger(__name__)
        self.task_manager = task_manager
        self.execution_log: List[Dict[str, Any]] = []

        self.is_running = False
        self.monitored_symbols: set[str] = set()

        self.data_provider.add_callback(self._handle_market_data)
        self.signal_monitor.add_signal_callback(self._handle_signal_notification)

    def attach_task_manager(self, task_manager: "TaskManager") -> None:
        """附加任务管理器，用于执行实时信号。"""
        self.task_manager = task_manager

    def start_monitoring(
        self,
        symbols: List[str],
        strategies: Optional[Dict[str, BaseStrategy]] = None,
    ) -> None:
        """为指定标的启动轮询流程。"""
        if self.is_running:
            self.logger.log_warning("Realtime monitor already running")
            return

        connection_result = self.data_provider.connect()
        if connection_result is False:
            raise ConnectionError("Failed to connect realtime data provider")

        if strategies:
            for name, strategy in strategies.items():
                self.signal_monitor.add_strategy(name, strategy)

        self.data_provider.subscribe(symbols)
        self.monitored_symbols.update(symbols)
        self.is_running = True

        self.logger.log_system_event("Realtime monitoring started", ", ".join(symbols))
        self.notification_manager.send_notification(
            f"Realtime monitoring started\nSymbols: {', '.join(symbols)}",
            "Realtime Monitor",
        )

    def stop_monitoring(self) -> None:
        if not self.is_running:
            return
        self.data_provider.disconnect()
        self.is_running = False
        self.logger.log_system_event("Realtime monitoring stopped")
        self.notification_manager.send_notification(
            "Realtime monitoring stopped",
            "Realtime Monitor",
        )

    def add_symbol(self, symbol: str) -> None:
        if symbol not in self.monitored_symbols:
            self.data_provider.subscribe([symbol])
            self.monitored_symbols.add(symbol)
            self.logger.log_system_event("Added realtime symbol", symbol)

    def remove_symbol(self, symbol: str) -> None:
        if symbol in self.monitored_symbols:
            self.monitored_symbols.remove(symbol)
            self.logger.log_system_event("Removed realtime symbol", symbol)

    def get_monitoring_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "is_connected": bool(getattr(self.data_provider, "is_connected", getattr(self.data_provider, "_active", False))),
            "monitored_symbols": sorted(self.monitored_symbols),
            "strategy_count": len(self.signal_monitor.strategies),
            "recent_signals": len(self.signal_monitor.signal_history[-10:]),
        }

    def get_market_summary(self) -> Dict[str, Any]:
        signals = self.signal_monitor.get_latest_signals(limit=50)
        distribution: Dict[str, int] = {}
        for signal in signals:
            distribution[signal.signal_type] = distribution.get(signal.signal_type, 0) + 1

        active_symbols = sorted({signal.symbol for signal in signals[-20:]})

        return {
            "total_signals": len(signals),
            "signal_distribution": distribution,
            "active_symbols": active_symbols,
            "last_update": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _handle_market_data(self, data: MarketData) -> None:
        """
        对实时数据提供器的内部回调：转发行情到信号监控器，同时同步未结订单状态。
        """
        self.signal_monitor.process_market_data(data)
        self._sync_order_updates()

    def _handle_signal_notification(self, signal: TradingSignal) -> None:
        if signal.signal_type in {"BUY", "SELL"} and signal.confidence >= 0.7:
            message = (
                f"Symbol: {signal.symbol}\n"
                f"Action: {signal.signal_type}\n"
                f"Strength: {signal.strength:.2f}\n"
                f"Price: {signal.price:.2f}\n"
                f"Strategy: {signal.strategy_name}\n"
                f"Time: {signal.timestamp:%H:%M:%S}"
            )

            execution_result = self._execute_signal(signal)
            if execution_result:
                status_line = f"Execution: {execution_result.get('status', 'unknown')}"
                risk_line = execution_result.get("risk_check")
                if risk_line:
                    status_line += f" | Risk: {risk_line}"
                message += f"\n{status_line}"
                if execution_result.get("order_id"):
                    message += f"\nOrder ID: {execution_result['order_id']}"

            self.notification_manager.send_notification(
                message, f"Realtime Signal - {signal.symbol}"
            )

    def _execute_signal(self, signal: TradingSignal) -> Optional[Dict[str, Any]]:
        if not self.task_manager:
            return None

        action = signal.signal_type.lower()
        if action not in {"buy", "sell"}:
            return None

        metadata = signal.metadata or {}
        result = self.task_manager.process_realtime_signal(
            symbol=signal.symbol,
            strategy_name=signal.strategy_name,
            action=action,
            signal_strength=signal.strength,
            confidence=signal.confidence,
            reason=metadata.get("reason", ""),
            target_price=metadata.get("target_price"),
            metadata=metadata,
        )
        result["received_at"] = datetime.now(timezone.utc).isoformat()
        self.execution_log.append(result)
        return result

    def _sync_order_updates(self) -> None:
        """
        轮询任务管理器的订单更新，并将结果写入执行日志及通知渠道。
        """
        if not self.task_manager:
            return

        updates = self.task_manager.reconcile_orders()
        if not updates:
            return

        timestamp = datetime.now(timezone.utc).isoformat()
        for update in updates:
            record = {"event": "order_update", "timestamp": timestamp, **update}
            self.execution_log.append(record)

            status = str(update.get("status", "")).lower()
            order_info = update.get("order") or {}
            symbol = order_info.get("symbol") or update.get("order_id", "")

            self.logger.log_system_event(
                "Realtime order update",
                f"{update.get('order_id')} -> {status.upper()}",
            )

            if status in {"filled", "partial_filled", "cancelled", "rejected"}:
                quantity = order_info.get("filled_quantity") or order_info.get("quantity") or 0
                price = order_info.get("filled_price")
                risk_info = update.get("risk_snapshot") or {}
                equity = risk_info.get("equity")
                cash = risk_info.get("cash")
                lines = [
                    f"Order: {update.get('order_id')}",
                    f"Status: {status.upper()}",
                    f"Symbol: {symbol}",
                ]
                if quantity:
                    lines.append(f"Quantity: {quantity}")
                if price is not None:
                    lines.append(f"Price: {price:.2f}")
                if equity is not None:
                    lines.append(f"Equity: {equity:,.2f}")
                if cash is not None:
                    lines.append(f"Cash: {cash:,.2f}")

                self.notification_manager.send_notification(
                    "\n".join(lines),
                    f"Order Update - {symbol}",
                )
