"""
均值回归策略。

通过布林带与 RSI 指标识别价格的过度偏离，从而捕捉回归均值的机会。
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from .base_strategy import BaseStrategy, SignalType


class MeanReversionStrategy(BaseStrategy):
    """结合布林带与 RSI 的均值回归策略实现。"""

    def __init__(
        self,
        bb_period: int = 20,
        bb_std: float = 2.0,
        rsi_period: int = 14,
        rsi_oversold: float = 30,
        rsi_overbought: float = 70,
    ):
        """
        初始化策略参数。

        参数：
            bb_period: 布林带计算周期
            bb_std: 布林带标准差倍数
            rsi_period: RSI 计算周期
            rsi_oversold: RSI 超卖阈值
            rsi_overbought: RSI 超买阈值
        """
        super().__init__("Mean Reversion")
        self.set_parameters(
            bb_period=bb_period,
            bb_std=bb_std,
            rsi_period=rsi_period,
            rsi_oversold=rsi_oversold,
            rsi_overbought=rsi_overbought,
        )

    # ------------------------------------------------------------------ #
    # 信号生成
    # ------------------------------------------------------------------ #
    def generate_signals(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """
        根据布林带与 RSI 指标生成交易信号。

        策略逻辑：
            - 价格接近下轨且 RSI 低于超卖阈值时，发出买入信号；
            - 价格接近上轨且 RSI 高于超买阈值时，发出卖出信号；
            - 当价格回到布林带中轨时，平掉对应方向的仓位。

        参数：
            market_data: 含 OHLCV 字段的行情数据 DataFrame

        返回：
            包含信号、仓位及关键指标的 DataFrame
        """
        if not self.validate_data(market_data):
            raise ValueError("无效的数据格式，缺少必要的 OHLCV 字段。")

        df = market_data.copy()
        df.columns = [col.lower() for col in df.columns]

        bb_period = self.get_parameter("bb_period", 20)
        bb_std = self.get_parameter("bb_std", 2.0)
        rsi_period = self.get_parameter("rsi_period", 14)
        rsi_oversold = self.get_parameter("rsi_oversold", 30)
        rsi_overbought = self.get_parameter("rsi_overbought", 70)

        df = self._add_bollinger_bands(df, bb_period, bb_std)
        df = self._add_rsi(df, rsi_period)
        df = self._add_additional_indicators(df)

        (
            buy_condition,
            sell_condition,
            exit_long_condition,
            exit_short_condition,
        ) = self._get_conditions(df, rsi_oversold, rsi_overbought)

        signals, positions = self._generate_trade_signals(
            df,
            buy_condition,
            sell_condition,
            exit_long_condition,
            exit_short_condition,
        )

        df["signal"] = signals
        df["position"] = positions
        df["signal_strength"] = self._calculate_signal_strength(df)

        self.signals = df[
            ["close", "bb_upper", "bb_middle", "bb_lower", "rsi", "signal", "position"]
        ].copy()

        return df[
            [
                "signal",
                "position",
                "bb_upper",
                "bb_middle",
                "bb_lower",
                "rsi",
                "signal_strength",
            ]
        ]

    # ------------------------------------------------------------------ #
    # 指标计算
    # ------------------------------------------------------------------ #
    def _add_bollinger_bands(
        self, df: pd.DataFrame, bb_period: int, bb_std: float
    ) -> pd.DataFrame:
        """计算并附加布林带相关列。"""
        df["bb_middle"] = df["close"].rolling(window=bb_period).mean()
        rolling_std = df["close"].rolling(window=bb_period).std()
        df["bb_upper"] = df["bb_middle"] + rolling_std * bb_std
        df["bb_lower"] = df["bb_middle"] - rolling_std * bb_std
        df["bb_position"] = (df["close"] - df["bb_lower"]) / (
            df["bb_upper"] - df["bb_lower"]
        )
        return df

    def _add_rsi(self, df: pd.DataFrame, rsi_period: int) -> pd.DataFrame:
        """计算 RSI 指标。"""
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0.0).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(window=rsi_period).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - (100 / (1 + rs))
        return df

    def _add_additional_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算价格偏离与带宽等辅助指标。"""
        df["price_deviation"] = (df["close"] - df["bb_middle"]) / df["bb_middle"] * 100
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"] * 100
        return df

    # ------------------------------------------------------------------ #
    # 条件 & 信号生成
    # ------------------------------------------------------------------ #
    def _get_conditions(
        self, df: pd.DataFrame, rsi_oversold: float, rsi_overbought: float
    ) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """构造买卖与平仓条件。"""
        width_ma = df["bb_width"].rolling(50).mean()

        buy_condition = (
            (df["close"] <= df["bb_lower"] * 1.01)
            & (df["rsi"] < rsi_oversold)
            & (df["bb_width"] > width_ma)
        )
        sell_condition = (
            (df["close"] >= df["bb_upper"] * 0.99)
            & (df["rsi"] > rsi_overbought)
            & (df["bb_width"] > width_ma)
        )
        exit_long_condition = (df["close"] >= df["bb_middle"]) | (df["rsi"] >= 50)
        exit_short_condition = (df["close"] <= df["bb_middle"]) | (df["rsi"] <= 50)

        return buy_condition, sell_condition, exit_long_condition, exit_short_condition

    def _generate_trade_signals(
        self,
        df: pd.DataFrame,
        buy_condition: pd.Series,
        sell_condition: pd.Series,
        exit_long_condition: pd.Series,
        exit_short_condition: pd.Series,
    ) -> Tuple[List[int], List[int]]:
        """遍历数据逐条生成信号与仓位序列。"""
        current_position = 0
        signals: List[int] = []
        positions: List[int] = []

        for idx in range(len(df)):
            signal, current_position = self._get_signal(
                idx,
                current_position,
                buy_condition,
                sell_condition,
                exit_long_condition,
                exit_short_condition,
            )
            signals.append(signal)
            positions.append(current_position)

        return signals, positions

    def _get_signal(
        self,
        index: int,
        current_position: int,
        buy_condition: pd.Series,
        sell_condition: pd.Series,
        exit_long_condition: pd.Series,
        exit_short_condition: pd.Series,
    ) -> Tuple[int, int]:
        """根据当前仓位状态返回新的信号与仓位。"""
        if current_position == 0:
            return self._signal_flat(index, buy_condition, sell_condition)
        if current_position > 0:
            return self._signal_long(index, exit_long_condition, sell_condition)
        return self._signal_short(index, exit_short_condition, buy_condition)

    def _signal_flat(
        self, index: int, buy_condition: pd.Series, sell_condition: pd.Series
    ) -> Tuple[int, int]:
        if buy_condition.iloc[index]:
            return SignalType.BUY.value, 1
        if sell_condition.iloc[index]:
            return SignalType.SELL.value, -1
        return SignalType.HOLD.value, 0

    def _signal_long(
        self,
        index: int,
        exit_condition: pd.Series,
        reverse_condition: pd.Series,
    ) -> Tuple[int, int]:
        if reverse_condition.iloc[index]:
            return SignalType.SELL.value, -1
        if exit_condition.iloc[index]:
            return SignalType.HOLD.value, 0
        return SignalType.HOLD.value, 1

    def _signal_short(
        self,
        index: int,
        exit_condition: pd.Series,
        reverse_condition: pd.Series,
    ) -> Tuple[int, int]:
        if reverse_condition.iloc[index]:
            return SignalType.BUY.value, 1
        if exit_condition.iloc[index]:
            return SignalType.HOLD.value, 0
        return SignalType.HOLD.value, -1

    def _calculate_signal_strength(self, df: pd.DataFrame) -> pd.Series:
        """以价格偏离布林带中轨的程度衡量信号强度。"""
        deviation = np.abs(df["price_deviation"])
        normalized = deviation / (df["bb_width"].replace(0, np.nan))
        return normalized.fillna(0).clip(upper=1.0)

    # ------------------------------------------------------------------ #
    # 过滤器
    # ------------------------------------------------------------------ #
    def add_volume_filter(
        self, market_data: pd.DataFrame, window: int = 20
    ) -> pd.DataFrame:
        """
        添加成交量过滤条件，过滤掉量能不足的信号。

        参数：
            market_data: 原始行情数据
            window: 成交量均线周期

        返回：
            含过滤结果的 DataFrame
        """
        df = market_data.copy()
        df.columns = [col.lower() for col in df.columns]

        df["volume_ma"] = df["volume"].rolling(window=window).mean()
        df["volume_filter"] = df["volume"] > df["volume_ma"]
        df.loc[~df["volume_filter"], "signal"] = SignalType.HOLD.value
        return df

    def add_trend_filter(
        self, market_data: pd.DataFrame, trend_period: int = 50
    ) -> pd.DataFrame:
        """
        添加趋势过滤，避免在强趋势中逆势操作。

        参数：
            market_data: 含信号的行情数据
            trend_period: 趋势均线周期

        返回：
            应用趋势过滤后的 DataFrame
        """
        df = market_data.copy()
        df.columns = [col.lower() for col in df.columns]
        df["trend_ma"] = df["close"].rolling(window=trend_period).mean()

        strong_uptrend = df["close"] > df["trend_ma"] * 1.05
        strong_downtrend = df["close"] < df["trend_ma"] * 0.95

        df.loc[(df["signal"] == SignalType.BUY.value) & strong_downtrend, "signal"] = (
            SignalType.HOLD.value
        )
        df.loc[(df["signal"] == SignalType.SELL.value) & strong_uptrend, "signal"] = (
            SignalType.HOLD.value
        )
        return df

    # ------------------------------------------------------------------ #
    # 参数优化与描述
    # ------------------------------------------------------------------ #
    def optimize_parameters(
        self,
        market_data: pd.DataFrame,
        bb_period_range: Tuple[int, int] = (10, 30),
        rsi_period_range: Tuple[int, int] = (10, 20),
        rsi_threshold_range: Tuple[int, int] = (20, 40),
    ) -> Dict[str, Any]:
        """
        简单网格搜索优化策略参数。

        返回：
            包含最佳参数、最佳收益与所有组合结果的字典
        """
        best_params: Dict[str, Any] = {}
        best_return = -float("inf")
        param_results: List[Dict[str, Any]] = []

        for bb_period in range(bb_period_range[0], bb_period_range[1] + 1, 2):
            for rsi_period in range(rsi_period_range[0], rsi_period_range[1] + 1, 2):
                for rsi_threshold in range(
                    rsi_threshold_range[0], rsi_threshold_range[1] + 1, 5
                ):
                    self.set_parameters(
                        bb_period=bb_period,
                        rsi_period=rsi_period,
                        rsi_oversold=rsi_threshold,
                        rsi_overbought=100 - rsi_threshold,
                    )
                    try:
                        backtest_results = self.backtest(market_data)
                        total_return = backtest_results.get("total_return", 0.0)
                    except (ValueError, KeyError):
                        continue

                    param_results.append(
                        {
                            "bb_period": bb_period,
                            "rsi_period": rsi_period,
                            "rsi_threshold": rsi_threshold,
                            "total_return": total_return,
                        }
                    )

                    if total_return > best_return:
                        best_return = total_return
                        best_params = {
                            "bb_period": bb_period,
                            "rsi_period": rsi_period,
                            "rsi_oversold": rsi_threshold,
                            "rsi_overbought": 100 - rsi_threshold,
                        }

        return {
            "best_parameters": best_params,
            "best_return": best_return,
            "all_results": param_results,
        }

    def get_strategy_description(self) -> str:
        """返回中文描述，便于调试或展示。"""
        bb_period = self.get_parameter("bb_period", 20)
        bb_std = self.get_parameter("bb_std", 2.0)
        rsi_period = self.get_parameter("rsi_period", 14)
        rsi_oversold = self.get_parameter("rsi_oversold", 30)
        rsi_overbought = self.get_parameter("rsi_overbought", 70)

        return (
            "均值回归策略\n"
            "------------------------------\n"
            f"布林带：周期 {bb_period}，标准差 {bb_std}\n"
            f"RSI：周期 {rsi_period}，阈值 {rsi_oversold}/{rsi_overbought}\n"
            "规则：靠近下轨买入、靠近上轨卖出，回到中轨平仓\n"
            "适用：震荡或箱体行情；趋势行情可能产生较多假信号。\n"
        )


if __name__ == "__main__":
    from ..data_provider import DataFetcher

    fetcher = DataFetcher()
    data = fetcher.fetch_stock_data(
        "AAPL", start_date="2022-01-01", end_date="2023-12-31"
    )

    strategy = MeanReversionStrategy()
    signals = strategy.generate_signals(data)

    print(strategy.get_strategy_description())
    print("\n前十条信号：")
    print(signals.head(10))

    results = strategy.backtest(data)
    print("\n回测结果：")
    print(f"总收益率: {results['total_return']:.2%}")
    print(f"期末资金: ${results['final_capital']:,.2f}")
