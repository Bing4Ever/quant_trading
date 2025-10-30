#!/usr/bin/env python3
"""
实时行情轮询提供器。

仅承担轮询调度与回调分发，具体的数据获取均委托给 TradingAgent 中的
``DataProvider``/``DataFetcher``，避免在服务层直接耦合外部行情 API。
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional

from src.common.logger import TradingLogger
from src.tradingagent.modules.data_provider import DataProvider

from .automation_models import MarketData


class RealTimeDataProvider:
    """轮询式行情数据提供器的基类。"""

    def __init__(self) -> None:
        self.is_connected = False
        self.callbacks: List[Callable[[MarketData], None]] = []

    def add_callback(self, callback: Callable[[MarketData], None]) -> None:
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def notify_callbacks(self, data: MarketData) -> None:
        logger = TradingLogger(__name__)
        for callback in list(self.callbacks):
            try:
                callback(data)
            except Exception as exc:  # pragma: no cover
                logger.log_error("Realtime callback failed", str(exc))

    def connect(self) -> bool:  # pragma: no cover - abstract
        raise NotImplementedError

    def disconnect(self) -> None:  # pragma: no cover - abstract
        raise NotImplementedError

    def subscribe(self, symbols: List[str]) -> None:  # pragma: no cover - abstract
        raise NotImplementedError


class PollingDataProvider(RealTimeDataProvider):
    """基于 TradingAgent ``DataProvider`` 的默认轮询实现。"""

    def __init__(self, poll_interval: int = 5, provider: Optional[str] = None) -> None:
        super().__init__()
        self.poll_interval = poll_interval
        self.subscribed_symbols: set[str] = set()
        self.polling_thread: Optional[threading.Thread] = None
        self.stop_polling = threading.Event()
        self.logger = TradingLogger(__name__)
        self.data_provider = DataProvider(provider=provider)

        self._last_prices: Dict[str, float] = {}
        self._last_volume: Dict[str, int] = {}
        self._volume_refresh: Dict[str, datetime] = {}
        self._volume_refresh_interval = timedelta(minutes=5)

    def connect(self) -> bool:
        """测试上游数据源连接以确认凭证有效。"""
        try:
            price = float(self.data_provider.get_current_price("SPY"))
            if price > 0:
                self.is_connected = True
                self.logger.log_system_event("Polling data provider connected")
                return True
        except Exception as exc:  # pragma: no cover
            self.logger.log_error("Polling provider connect failed", str(exc))
        return False

    def disconnect(self) -> None:
        """停止轮询并标记数据源离线。"""
        if self.polling_thread and self.polling_thread.is_alive():
            self.stop_polling.set()
            self.polling_thread.join()
        self.is_connected = False
        self.logger.log_system_event("Polling data provider disconnected")

    def subscribe(self, symbols: List[str]) -> None:
        """登记需要轮询的标的列表。"""
        for symbol in symbols:
            if symbol not in self.subscribed_symbols:
                self._prime_symbol_state(symbol)
                self.subscribed_symbols.add(symbol)

        if self.is_connected and not (
            self.polling_thread and self.polling_thread.is_alive()
        ):
            self.stop_polling.clear()
            self.polling_thread = threading.Thread(
                target=self._polling_loop,
                name="MarketDataPolling",
                daemon=True,
            )
            self.polling_thread.start()
            self.logger.log_system_event("Started monitoring symbols", ", ".join(symbols))

    def _polling_loop(self) -> None:
        while not self.stop_polling.is_set():
            try:
                for symbol in list(self.subscribed_symbols):
                    snapshot = self._fetch_latest_data(symbol)
                    if snapshot:
                        self.notify_callbacks(snapshot)
                time.sleep(self.poll_interval)
            except Exception as exc:  # pragma: no cover
                self.logger.log_error("Polling loop error", str(exc))
                time.sleep(5.0)

    def _prime_symbol_state(self, symbol: str) -> None:
        try:
            end_dt = datetime.now(timezone.utc)
            start_dt = end_dt - timedelta(minutes=30)
            history = self.data_provider.get_historical_data(
                symbol=symbol,
                start_date=start_dt.strftime("%Y-%m-%d"),
                end_date=end_dt.strftime("%Y-%m-%d"),
                interval="1m",
            )
            if history is not None and not history.empty:
                frame = history.copy()
                frame.columns = [str(col).lower() for col in frame.columns]
                latest = frame.iloc[-1]
                self._last_prices[symbol] = float(latest.get("close", latest.iloc[-1]))
                self._last_volume[symbol] = int(latest.get("volume", 0) or 0)
                self._volume_refresh[symbol] = end_dt
        except Exception as exc:  # pragma: no cover
            self.logger.log_error("Prime state failed", f"{symbol}: {exc}")

    def _fetch_latest_data(self, symbol: str) -> Optional[MarketData]:
        try:
            price = float(self.data_provider.get_current_price(symbol))
            if price <= 0:
                return None

            previous = self._last_prices.get(symbol, price)
            change = price - previous
            change_percent = (change / previous * 100.0) if previous else 0.0
            self._last_prices[symbol] = price

            volume = self._last_volume.get(symbol, 0)
            last_refresh = self._volume_refresh.get(
                symbol, datetime.min.replace(tzinfo=timezone.utc)
            )
            if datetime.now(timezone.utc) - last_refresh >= self._volume_refresh_interval:
                refreshed = self._refresh_volume(symbol)
                if refreshed is not None:
                    volume = refreshed

            return MarketData(
                symbol=symbol,
                price=price,
                volume=volume,
                change=change,
                change_percent=change_percent,
                timestamp=datetime.now(timezone.utc),
            )
        except Exception as exc:  # pragma: no cover
            self.logger.log_error("Snapshot creation failed", f"{symbol}: {exc}")
            return None

    def _refresh_volume(self, symbol: str) -> Optional[int]:
        try:
            end_dt = datetime.now(timezone.utc)
            start_dt = end_dt - timedelta(minutes=5)
            history = self.data_provider.get_historical_data(
                symbol=symbol,
                start_date=start_dt.strftime("%Y-%m-%d"),
                end_date=end_dt.strftime("%Y-%m-%d"),
                interval="1m",
            )
            if history is None or history.empty:
                return None

            frame = history.copy()
            frame.columns = [str(col).lower() for col in frame.columns]
            latest = frame.iloc[-1]
            volume = int(latest.get("volume", 0) or 0)
            self._last_volume[symbol] = volume
            self._volume_refresh[symbol] = end_dt
            return volume
        except Exception as exc:  # pragma: no cover
            self.logger.log_error("Volume refresh failed", f"{symbol}: {exc}")
            return None
