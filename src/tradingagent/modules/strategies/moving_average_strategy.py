"""
均线交叉策略。

经典趋势跟随策略：短期均线向上突破长期均线时看多，反向穿越时退出或反向。
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from .base_strategy import BaseStrategy, SignalType


class MovingAverageStrategy(BaseStrategy):
    """基于均线交叉的趋势跟随策略。"""

    def __init__(
        self,
        short_window: int = 20,
        long_window: int = 50,
        ma_type: str = "sma",
    ):
        """
        初始化策略参数。

        参数：
            short_window: 短周期均线长度
            long_window: 长周期均线长度
            ma_type: 均线类型，支持 `sma` 或 `ema`
        """
        super().__init__("Moving Average Crossover")
        self.set_parameters(
            short_window=short_window, long_window=long_window, ma_type=ma_type
        )

    # ------------------------------------------------------------------ #
    # 核心信号逻辑
    # ------------------------------------------------------------------ #
    def generate_signals(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """
        根据均线交叉生成买卖信号。

        策略规则：
            - 短均线向上穿越长均线：买入信号；
            - 短均线向下穿越长均线：卖出/平仓信号；
            - 其他情况保持现有仓位。

        参数：
            market_data: 含 OHLCV 字段的行情数据表

        返回：
            包含信号、仓位及辅助指标的 DataFrame
        """
        if not self.validate_data(market_data):
            raise ValueError("行情数据缺失必需的 OHLCV 字段。")

        df = market_data.copy()
        df.columns = [col.lower() for col in df.columns]

        short_window = self.get_parameter("short_window", 20)
        long_window = self.get_parameter("long_window", 50)
        ma_type = self.get_parameter("ma_type", "sma").lower()

        if ma_type not in {"sma", "ema"}:
            raise ValueError(f"不支持的均线类型: {ma_type}")

        if ma_type == "sma":
            df["short_ma"] = df["close"].rolling(window=short_window).mean()
            df["long_ma"] = df["close"].rolling(window=long_window).mean()
        else:
            df["short_ma"] = df["close"].ewm(span=short_window, adjust=False).mean()
            df["long_ma"] = df["close"].ewm(span=long_window, adjust=False).mean()

        df["signal"] = SignalType.HOLD.value
        df["position"] = 0

        crossover = (
            (df["short_ma"] > df["long_ma"])
            & (df["short_ma"].shift(1) <= df["long_ma"].shift(1))
        )
        crossunder = (
            (df["short_ma"] < df["long_ma"])
            & (df["short_ma"].shift(1) >= df["long_ma"].shift(1))
        )

        df.loc[crossover, "signal"] = SignalType.BUY.value
        df.loc[crossunder, "signal"] = SignalType.SELL.value

        current_position = 0
        positions = []
        for signal in df["signal"]:
            if signal == SignalType.BUY.value:
                current_position = 1
            elif signal == SignalType.SELL.value:
                current_position = 0
            positions.append(current_position)
        df["position"] = positions

        df["ma_spread"] = df["short_ma"] - df["long_ma"]
        df["ma_spread_pct"] = (
            df["ma_spread"] / df["long_ma"].replace(0, np.nan)
        ).fillna(0) * 100

        self.signals = df[
            ["close", "short_ma", "long_ma", "signal", "position", "ma_spread"]
        ].copy()

        return df[["signal", "position", "short_ma", "long_ma", "ma_spread"]]

    # ------------------------------------------------------------------ #
    # 过滤与辅助工具
    # ------------------------------------------------------------------ #
    def add_trend_filter(
        self, signal_data: pd.DataFrame, trend_window: int = 200
    ) -> pd.DataFrame:
        """
        添加长周期趋势过滤，避免在弱趋势下频繁交易。

        参数：
            signal_data: 含信号的行情数据
            trend_window: 趋势均线长度

        返回：
            应用趋势过滤后的数据
        """
        df = signal_data.copy()
        df.columns = [col.lower() for col in df.columns]

        df["trend_ma"] = df["close"].rolling(window=trend_window).mean()
        df["trend_filter"] = df["close"] > df["trend_ma"]

        df.loc[
            (df["signal"] == SignalType.BUY.value) & (~df["trend_filter"]), "signal"
        ] = SignalType.HOLD.value
        df.loc[(df["position"].shift(1) == 1) & (~df["trend_filter"]), "signal"] = (
            SignalType.SELL.value
        )
        return df

    def add_volatility_filter(
        self, signal_data: pd.DataFrame, window: int = 20
    ) -> pd.DataFrame:
        """
        添加波动率过滤，仅在波动率超过均值时执行策略。

        参数：
            signal_data: 含信号的行情数据
            window: 波动率均线窗口
        """
        df = signal_data.copy()
        df.columns = [col.lower() for col in df.columns]

        df["returns"] = df["close"].pct_change().fillna(0)
        df["volatility"] = df["returns"].rolling(window=window).std() * np.sqrt(252)
        df["volatility_threshold"] = df["volatility"].rolling(window).mean()
        df["volatility_filter"] = df["volatility"] > df["volatility_threshold"]

        df.loc[~df["volatility_filter"], "signal"] = SignalType.HOLD.value
        return df

    # ------------------------------------------------------------------ #
    # 参数优化与描述
    # ------------------------------------------------------------------ #
    def optimize_parameters(
        self,
        market_data: pd.DataFrame,
        short_range: Tuple[int, int] = (5, 50),
        long_range: Tuple[int, int] = (20, 200),
        step: int = 5,
    ) -> Dict[str, Any]:
        """
        通过网格搜索寻找最佳短长均线组合。

        返回：
            包含最佳参数及收益表现的字典
        """
        best_params: Dict[str, Any] = {}
        best_return = -float("inf")
        optimization_results = []

        for short_window in range(short_range[0], short_range[1] + 1, step):
            for long_window in range(long_range[0], long_range[1] + 1, step):
                if short_window >= long_window:
                    continue

                self.set_parameters(short_window=short_window, long_window=long_window)
                try:
                    result = self.backtest(market_data)
                except (ValueError, KeyError):
                    continue

                total_return = result.get("total_return", 0.0)
                optimization_results.append(
                    {
                        "short_window": short_window,
                        "long_window": long_window,
                        "total_return": total_return,
                    }
                )

                if total_return > best_return:
                    best_return = total_return
                    best_params = {
                        "short_window": short_window,
                        "long_window": long_window,
                    }

        return {
            "best_parameters": best_params,
            "best_return": best_return,
            "all_results": optimization_results,
        }

    def get_strategy_description(self) -> str:
        """返回中文描述，便于展示或调试。"""
        short_window = self.get_parameter("short_window", 20)
        long_window = self.get_parameter("long_window", 50)
        ma_type = self.get_parameter("ma_type", "sma").upper()

        return (
            "均线交叉策略\n"
            "------------------------------\n"
            f"类型：趋势跟随\n"
            f"短均线：{short_window} （{ma_type}）\n"
            f"长均线：{long_window} （{ma_type}）\n"
            "规则：短期向上突破买入，向下跌破卖出\n"
            "适用：趋势行情；在震荡市可能产生较多假信号。\n"
        )


if __name__ == "__main__":
    from ..data_provider import DataFetcher

    fetcher = DataFetcher()
    data = fetcher.fetch_stock_data(
        "AAPL", start_date="2022-01-01", end_date="2023-12-31"
    )

    strategy = MovingAverageStrategy(short_window=20, long_window=50)
    signals = strategy.generate_signals(data)

    print(strategy.get_strategy_description())
    print("\n前十条信号：")
    print(signals.head(10))

    results = strategy.backtest(data)
    print("\n回测结果：")
    print(f"总收益率: {results['total_return']:.2%}")
    print(f"期末资金: ${results['final_capital']:,.2f}")
