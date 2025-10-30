"""
 布林带交易策略。

 基于布林带突破生成买卖信号，并支持少量参数配置。
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd

from .base_strategy import BaseStrategy
from .strategies_models import SignalType


class BollingerBandsStrategy(BaseStrategy):
    """基于布林带突破的简易策略实现。"""

    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__(name="BollingerBandsStrategy")
        self.period = period
        self.std_dev = std_dev

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """统一字段名称并计算布林带。"""
        df = data.copy()
        df.columns = [col.lower() for col in df.columns]

        df["middle_band"] = df["close"].rolling(window=self.period).mean()
        rolling_std = df["close"].rolling(window=self.period).std()
        df["upper_band"] = df["middle_band"] + rolling_std * self.std_dev
        df["lower_band"] = df["middle_band"] - rolling_std * self.std_dev

        return df

    # ------------------------------------------------------------------ #
    # BaseStrategy overrides
    # ------------------------------------------------------------------ #
    def generate_signals(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """依据布林带突破规则生成交易信号。"""
        df = self._prepare_data(market_data)

        signals = pd.DataFrame(index=df.index)
        signals["price"] = df["close"]
        signals["signal"] = 0

        # 入场条件
        signals.loc[df["close"] <= df["lower_band"], "signal"] = SignalType.BUY.value
        signals.loc[df["close"] >= df["upper_band"], "signal"] = SignalType.SELL.value

        # 可选出场/中性规则：回到上下轨之间后平仓
        neutral_mask = (df["close"] > df["lower_band"]) & (df["close"] < df["upper_band"])
        signals.loc[neutral_mask, "signal"] = SignalType.HOLD.value

        # 跟踪持仓状态
        signals["position"] = signals["signal"].replace(
            {0: np.nan}
        ).ffill().fillna(0).astype(int)

        # 下游可用的辅助布尔标记
        signals["buy_signal"] = signals["signal"] == SignalType.BUY.value
        signals["sell_signal"] = signals["signal"] == SignalType.SELL.value

        return signals

    def validate_data(self, data: pd.DataFrame) -> bool:
        """确保数据包含 OHLCV 字段且历史长度充足。"""
        try:
            if data is None or data.empty:
                return False

            normalized = [col.lower() for col in data.columns]
            required = {"open", "high", "low", "close", "volume"}
            if not required.issubset(normalized):
                return False

            if len(data) < self.period + 5:
                return False

            close_series = data["Close"] if "Close" in data.columns else data["close"]
            if close_series.isna().mean() > 0.1:
                return False

            return True
        except Exception:
            return False

    def get_parameters(self) -> Dict[str, Any]:
        """暴露可配置参数。"""
        return {
            "period": self.period,
            "std_dev": self.std_dev,
            "strategy_type": "BollingerBands",
        }

    def set_parameters(self, **kwargs) -> None:
        """允许外部更新策略参数。"""
        if "period" in kwargs and kwargs["period"] > 0:
            self.period = int(kwargs["period"])
        if "std_dev" in kwargs and kwargs["std_dev"] > 0:
            self.std_dev = float(kwargs["std_dev"])
