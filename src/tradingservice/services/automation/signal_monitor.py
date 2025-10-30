#!/usr/bin/env python3
"""
实时行情信号监控组件。
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional

import pandas as pd

from src.common.logger import TradingLogger
from src.tradingagent.modules.strategies import BaseStrategy
from src.tradingagent.modules.data_provider import DataProvider

from .automation_models import MarketData, TradingSignal


class SignalMonitor:
    """跟踪已注册策略并生成高层信号摘要。"""

    def __init__(
        self,
        *,
        data_provider: Optional[DataProvider] = None,
        lookback_minutes: int = 180,
    ) -> None:
        self.strategies: Dict[str, BaseStrategy] = {}
        self.signal_history: List[TradingSignal] = []
        self.signal_callbacks: List[Callable[[TradingSignal], None]] = []
        self.logger = TradingLogger(__name__)
        self._lock = threading.Lock()
        self.data_provider = data_provider or DataProvider()
        self.lookback_window = max(lookback_minutes, 30)

    def add_strategy(self, name: str, strategy: BaseStrategy) -> None:
        self.strategies[name] = strategy
        self.logger.log_system_event("Strategy registered for realtime monitor", name)

    def remove_strategy(self, name: str) -> None:
        if name in self.strategies:
            del self.strategies[name]
            self.logger.log_system_event("Strategy removed from realtime monitor", name)

    def add_signal_callback(self, callback: Callable[[TradingSignal], None]) -> None:
        if callback not in self.signal_callbacks:
            self.signal_callbacks.append(callback)

    def process_market_data(self, data: MarketData) -> None:
        """将原始行情转换为结构化交易信号。"""
        with self._lock:
            try:
                signals = self._generate_signals(data)
                for signal in signals:
                    self.signal_history.append(signal)
                    for callback in list(self.signal_callbacks):
                        try:
                            callback(signal)
                        except Exception as exc:  # pragma: no cover
                            self.logger.log_error("Signal callback failed", str(exc))
            except Exception as exc:  # pragma: no cover
                self.logger.log_error("Signal processing failed", str(exc))

    def _generate_signals(self, data: MarketData) -> List[TradingSignal]:
        """根据价格动量生成基础信号。"""
        signals: List[TradingSignal] = []

        for name, strategy in self.strategies.items():
            try:
                historical = self._build_minute_frame(data.symbol)
                if historical.empty:
                    continue
                result = strategy.generate_signals(historical.tail(100))
                if result is None or result.empty or "signal" not in result.columns:
                    continue
                latest_row = result.iloc[-1]
                latest_signal = latest_row.get("signal")
                if pd.isna(latest_signal):
                    continue
                if latest_signal == 0:
                    continue
                direction = "BUY" if latest_signal > 0 else "SELL"
                strength = min(1.0, abs(float(latest_signal)))
                strategy_label = getattr(strategy, "name", name)
                reason_text = f"{strategy_label}实时信号"
                metadata = {"source": "strategy", "reason": reason_text}
                target_price = latest_row.get("target_price")
                if pd.notna(target_price):
                    metadata["target_price"] = float(target_price)

                signals.append(
                    TradingSignal(
                        symbol=data.symbol,
                        signal_type=direction,
                        strength=strength,
                        price=data.price,
                        timestamp=datetime.now(timezone.utc),
                        strategy_name=name,
                        confidence=strength,
                        metadata=metadata,
                    )
                )
            except Exception as exc:  # pragma: no cover
                self.logger.log_error("Strategy signal failed", f"{name}: {exc}")

        if not signals and data.change_percent is not None:
            if data.change_percent > 1.0:
                direction = "BUY"
                strength = min(1.0, data.change_percent / 5.0)
            elif data.change_percent < -1.0:
                direction = "SELL"
                strength = min(1.0, abs(data.change_percent) / 5.0)
            else:
                direction = "HOLD"
                strength = 0.0

            if direction != "HOLD":
                metadata = {
                    "source": "momentum",
                    "reason": "Momentum heuristic realtime signal",
                    "change_percent": data.change_percent,
                }
                signals.append(
                    TradingSignal(
                        symbol=data.symbol,
                        signal_type=direction,
                        strength=strength,
                        price=data.price,
                        timestamp=datetime.now(timezone.utc),
                        strategy_name="momentum",
                        confidence=strength,
                        metadata=metadata,
                    )
                )

        return signals

    def _build_minute_frame(self, symbol: str) -> pd.DataFrame:
        """构造最近的日内数据框架（可在子类中覆盖）。"""
        try:
            end_dt = datetime.now(timezone.utc)
            lookback_delta = timedelta(minutes=self.lookback_window)
            start_dt = end_dt - lookback_delta

            lookback_days = max(1, int(lookback_delta.total_seconds() // 86400) + 1)
            fetch_start = (end_dt - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
            fetch_end = end_dt.strftime("%Y-%m-%d")

            data = self.data_provider.get_historical_data(
                symbol=symbol,
                start_date=fetch_start,
                end_date=fetch_end,
                interval="1m",
            )
            if data is None or data.empty:
                return pd.DataFrame()

            frame = data.copy()
            frame.index = pd.to_datetime(frame.index)
            if frame.index.tz is not None:
                frame.index = frame.index.tz_convert("UTC").tz_localize(None)
            frame = frame.sort_index()
            cutoff = (end_dt - lookback_delta).replace(tzinfo=None)
            frame = frame.loc[frame.index >= cutoff]
            frame.columns = [str(col).lower() for col in frame.columns]
            return frame
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.log_error("Failed to build intraday frame", f"{symbol}: {exc}")
            return pd.DataFrame()

    def get_latest_signals(self, limit: int = 10) -> List[TradingSignal]:
        return self.signal_history[-limit:]
