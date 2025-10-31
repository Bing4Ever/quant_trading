#!/usr/bin/env python3
"""
实时交易运行时：串联实时行情监控、任务管理器与经纪商执行链路。

该模块提供轻量封装，复用实时监控与任务管理链路，将订单发往配置的经纪商
（默认 Alpaca），并将订单对账结果暴露给上层消费（UI、通知等）。
"""

from __future__ import annotations

from typing import Dict, List, Optional

from src.common.logger import TradingLogger
from src.tradingagent.core import IBroker
from src.tradingagent.core.brokers import BrokerFactory
from src.tradingagent.modules.strategies import BaseStrategy

from config import config as app_config

from .realtime_provider import PollingDataProvider, RealTimeDataProvider
from .real_time_monitor import RealTimeMonitor
from ..orchestration import TaskManager


class LiveTradingRuntime:
    """
    实时交易运行时：将实时行情监控与任务管理/执行管线绑定至指定经纪商。
    """

    def __init__(
        self,
        *,
        broker: Optional[IBroker] = None,
        broker_id: Optional[str] = None,
        data_provider: Optional[RealTimeDataProvider] = None,
        provider: Optional[str] = None,
        poll_interval: int = 5,
    ) -> None:
        self.logger = TradingLogger(__name__)
        self._broker_id = broker_id
        self.provider = provider or app_config.get(
            "market_data.default_provider", "alpaca"
        )

        self.broker = broker or self._create_broker()
        if not self.broker.is_connected():
            self.broker.connect()

        self.data_provider = data_provider or PollingDataProvider(
            poll_interval=poll_interval, provider=self.provider
        )

        self.task_manager = TaskManager(broker=self.broker)
        self.monitor = RealTimeMonitor(
            data_provider=self.data_provider, task_manager=self.task_manager
        )

        self._symbols: List[str] = []
        self._strategies: Dict[str, BaseStrategy] = {}

        self.logger.log_system_event(
            "Live trading runtime initialised",
            f"provider={self.provider}",
        )

    def start(
        self,
        symbols: List[str],
        strategies: Optional[Dict[str, BaseStrategy]] = None,
    ) -> None:
        """
        启动指定标的与策略的实时监控。
        """
        self._symbols = list(symbols)
        self._strategies = dict(strategies or {})

        self.monitor.start_monitoring(symbols, strategies)
        self.logger.log_system_event(
            "Live trading runtime started", ", ".join(symbols)
        )

    def stop(self) -> None:
        """
        停止实时监控，并断开行情数据源。
        """
        self.monitor.stop_monitoring()
        self.logger.log_system_event("Live trading runtime stopped")

    def status(self) -> Dict[str, object]:
        """
        返回当前运行时的状态快照。
        """
        runtime_status = self.monitor.get_monitoring_status()
        runtime_status["provider"] = self.provider
        runtime_status["symbols"] = list(self._symbols)
        runtime_status["broker_connected"] = self.broker.is_connected()
        return runtime_status

    def reconcile_now(self) -> List[Dict[str, object]]:
        """
        立即触发一次未结订单对账。
        """
        return self.task_manager.reconcile_orders()

    def execution_log(self) -> List[Dict[str, object]]:
        """
        返回内部维护的执行日志。
        """
        return list(self.monitor.execution_log)

    def _create_broker(self) -> IBroker:
        broker_type, params = app_config.resolve_broker(self._broker_id)
        return BrokerFactory.create(broker_type, **params)
