"""
Mean Reversion Strategy.

A statistical arbitrage strategy that assumes prices will revert to their mean
over time. Uses Bollinger Bands and RSI to identify overbought/oversold conditions.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, SignalType


class MeanReversionStrategy(BaseStrategy):
    """
    Mean Reversion Strategy using Bollinger Bands and RSI.

    Parameters:
    -----------
    bb_period : int
        Period for Bollinger Bands calculation (default: 20)
    bb_std : float
        Standard deviation multiplier for Bollinger Bands (default: 2.0)
    rsi_period : int
        Period for RSI calculation (default: 14)
    rsi_oversold : float
        RSI oversold threshold (default: 30)
    rsi_overbought : float
        RSI overbought threshold (default: 70)
    """

    def __init__(
        self,
        bb_period: int = 20,
        bb_std: float = 2.0,
        rsi_period: int = 14,
        rsi_oversold: float = 30,
        rsi_overbought: float = 70,
    ):
        """
        Initialize Mean Reversion Strategy.

        Args:
            bb_period: Bollinger Bands period
            bb_std: Bollinger Bands standard deviation multiplier
            rsi_period: RSI calculation period
            rsi_oversold: RSI oversold threshold
            rsi_overbought: RSI overbought threshold
        """
        super().__init__("Mean Reversion")

        self.set_parameters(
            bb_period=bb_period,
            bb_std=bb_std,
            rsi_period=rsi_period,
            rsi_oversold=rsi_oversold,
            rsi_overbought=rsi_overbought,
        )

    def generate_signals(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate mean reversion signals based on Bollinger Bands and RSI.

        The strategy generates:
        - BUY signal when price touches lower Bollinger Band AND RSI < oversold
        - SELL signal when price touches upper Bollinger Band AND RSI > overbought
        - CLOSE signal when price returns to middle Bollinger Band

        Args:
            market_data: Market data DataFrame with OHLCV columns

        Returns:
            DataFrame with trading signals and indicators
        """
        if not self.validate_data(market_data):
            raise ValueError("Invalid data format")

        df = market_data.copy()

        # Get parameters
        bb_period = self.get_parameter("bb_period", 20)
        bb_std = self.get_parameter("bb_std", 2.0)
        rsi_period = self.get_parameter("rsi_period", 14)
        rsi_oversold = self.get_parameter("rsi_oversold", 30)
        rsi_overbought = self.get_parameter("rsi_overbought", 70)

        df = self._add_bollinger_bands(df, bb_period, bb_std)
        df = self._add_rsi(df, rsi_period)
        df = self._add_additional_indicators(df)

        buy_condition, sell_condition, exit_long_condition, exit_short_condition = self._get_conditions(
            df, rsi_oversold, rsi_overbought
        )

        df["signal"], df["position"] = self._generate_trade_signals(
            df, buy_condition, sell_condition, exit_long_condition, exit_short_condition
        )

        # Add signal strength
        df["signal_strength"] = self._calculate_signal_strength(df)

        # Store signals for later use
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

    def _add_bollinger_bands(self, df: pd.DataFrame, bb_period: int, bb_std: float) -> pd.DataFrame:
        df["bb_middle"] = df["close"].rolling(window=bb_period).mean()
        bb_rolling_std = df["close"].rolling(window=bb_period).std()
        df["bb_upper"] = df["bb_middle"] + (bb_rolling_std * bb_std)
        df["bb_lower"] = df["bb_middle"] - (bb_rolling_std * bb_std)
        df["bb_position"] = (df["close"] - df["bb_lower"]) / (
            df["bb_upper"] - df["bb_lower"]
        )
        return df

    def _add_rsi(self, df: pd.DataFrame, rsi_period: int) -> pd.DataFrame:
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))
        return df

    def _add_additional_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["price_deviation"] = (df["close"] - df["bb_middle"]) / df["bb_middle"] * 100
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"] * 100
        return df

    def _get_conditions(
        self, df: pd.DataFrame, rsi_oversold: float, rsi_overbought: float
    ):
        buy_condition = (
            (df["close"] <= df["bb_lower"] * 1.01)
            & (df["rsi"] < rsi_oversold)
            & (df["bb_width"] > df["bb_width"].rolling(50).mean())
        )
        sell_condition = (
            (df["close"] >= df["bb_upper"] * 0.99)
            & (df["rsi"] > rsi_overbought)
            & (df["bb_width"] > df["bb_width"].rolling(50).mean())
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
    ):
        current_position = 0
        positions = []
        signal_list = []

        for i in range(len(df)):
            signal, new_position = self._get_signal(
                i, current_position, buy_condition, sell_condition, exit_long_condition, exit_short_condition
            )
            signal_list.append(signal)
            positions.append(new_position)
            current_position = new_position

        return signal_list, positions

    def _get_signal(
        self,
        i: int,
        current_position: int,
        buy_condition: pd.Series,
        sell_condition: pd.Series,
        exit_long_condition: pd.Series,
        exit_short_condition: pd.Series,
    ):
        if current_position == 0:
            return self._signal_flat(i, buy_condition, sell_condition)
        elif current_position == 1:
            return self._signal_long(i, exit_long_condition, sell_condition)
        elif current_position == -1:
            return self._signal_short(i, exit_short_condition, buy_condition)
        else:
            return 0, 0

    def _signal_flat(self, i: int, buy_condition: pd.Series, sell_condition: pd.Series):
        if buy_condition.iloc[i]:
            return SignalType.BUY.value, 1
        if sell_condition.iloc[i]:
            return SignalType.SELL.value, -1
        return 0, 0

    def _signal_long(self, i: int, exit_long_condition: pd.Series, sell_condition: pd.Series):
        if exit_long_condition.iloc[i] or sell_condition.iloc[i]:
            return SignalType.SELL.value, 0
        return 0, 1

    def _signal_short(self, i: int, exit_short_condition: pd.Series, buy_condition: pd.Series):
        if exit_short_condition.iloc[i] or buy_condition.iloc[i]:
            return SignalType.BUY.value, 0
        return 0, -1

    def _calculate_signal_strength(self, indicators_df: pd.DataFrame) -> pd.Series:
        """
        Calculate signal strength based on how extreme the indicators are.

        Args:
            indicators_df: DataFrame with calculated indicators

        Returns:
            Series with signal strength values (0 to 1)
        """
        # RSI component
        rsi_strength = np.where(
            indicators_df["rsi"] < 30,
            (30 - indicators_df["rsi"]) / 30,  # Stronger when more oversold
            np.where(
                indicators_df["rsi"] > 70,
                (indicators_df["rsi"] - 70) / 30,  # Stronger when more overbought
                0,
            ),
        )

        # Bollinger Band component
        bb_strength = np.abs(indicators_df["bb_position"] - 0.5) * 2  # 0 at middle, 1 at bands

        # Combine components
        signal_strength = np.maximum(rsi_strength, bb_strength)

        return pd.Series(signal_strength, index=indicators_df.index)

    def add_volume_filter(
        self, market_data: pd.DataFrame, volume_ma_period: int = 20
    ) -> pd.DataFrame:
        """
        Add volume filter to improve signal quality.

        Only takes signals when volume is above average.

        Args:
            market_data: Market data with signals
            volume_ma_period: Period for volume moving average

        Returns:
            DataFrame with volume-filtered signals
        """
        df = market_data.copy()

        # Calculate volume moving average
        df["volume_ma"] = df["volume"].rolling(window=volume_ma_period).mean()
        df["volume_filter"] = df["volume"] > df["volume_ma"]

        # Apply volume filter to signals
        df.loc[~df["volume_filter"], "signal"] = 0

        return df

    def add_trend_filter(
        self, market_data: pd.DataFrame, trend_period: int = 50
    ) -> pd.DataFrame:
        """
        Add trend filter - avoid counter-trend trades in strong trends.

        Args:
            market_data: Market data with signals
            trend_period: Period for trend determination

        Returns:
            DataFrame with trend-filtered signals
        """
        df = market_data.copy()

        # Calculate trend
        df["trend_ma"] = df["close"].rolling(window=trend_period).mean()
        df["trend_direction"] = np.where(df["close"] > df["trend_ma"], 1, -1)

        # Reduce signal strength in strong trends
        strong_uptrend = df["close"] > df["trend_ma"] * 1.05
        strong_downtrend = df["close"] < df["trend_ma"] * 0.95

        # Reduce buy signals in strong downtrends
        df.loc[(df["signal"] == SignalType.BUY.value) & strong_downtrend, "signal"] = 0

        # Reduce sell signals in strong uptrends
        df.loc[(df["signal"] == SignalType.SELL.value) & strong_uptrend, "signal"] = 0

        return df

    def optimize_parameters(
        self,
        market_data: pd.DataFrame,
        bb_period_range: tuple = (10, 30),
        rsi_period_range: tuple = (10, 20),
        rsi_threshold_range: tuple = (20, 40),
    ) -> Dict[str, Any]:
        """
        Optimize strategy parameters.

        Args:
            market_data: Market data for optimization
            bb_period_range: Range for Bollinger Band period
            rsi_period_range: Range for RSI period
            rsi_threshold_range: Range for RSI thresholds

        Returns:
            Dictionary with best parameters and performance
        """
        best_params = {}
        best_return = -float("inf")
        param_results = []

        for bb_period in range(bb_period_range[0], bb_period_range[1] + 1, 2):
            for rsi_period in range(rsi_period_range[0], rsi_period_range[1] + 1, 2):
                for rsi_threshold in range(
                    rsi_threshold_range[0], rsi_threshold_range[1] + 1, 5
                ):

                    # Set parameters
                    self.set_parameters(
                        bb_period=bb_period,
                        rsi_period=rsi_period,
                        rsi_oversold=rsi_threshold,
                        rsi_overbought=100 - rsi_threshold,
                    )

                    try:
                        # Run backtest
                        backtest_results = self.backtest(market_data)
                        total_return = backtest_results["total_return"]

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

                    except (ValueError, KeyError) as e:
                        print(f"Error optimizing parameters: {e}")
                        continue

        return {
            "best_parameters": best_params,
            "best_return": best_return,
            "all_results": param_results,
        }

    def get_strategy_description(self) -> str:
        """Get strategy description."""
        bb_period = self.get_parameter("bb_period", 20)
        bb_std = self.get_parameter("bb_std", 2.0)
        rsi_period = self.get_parameter("rsi_period", 14)
        rsi_oversold = self.get_parameter("rsi_oversold", 30)
        rsi_overbought = self.get_parameter("rsi_overbought", 70)

        return f"""
        Mean Reversion Strategy
        ======================
        
        Type: Mean Reversion / Statistical Arbitrage
        Bollinger Bands: {bb_period} periods, {bb_std} std dev
        RSI: {rsi_period} periods
        RSI Thresholds: {rsi_oversold} (oversold) / {rsi_overbought} (overbought)
        
        Rules:
        - BUY when price near lower BB AND RSI < {rsi_oversold}
        - SELL when price near upper BB AND RSI > {rsi_overbought}
        - EXIT when price returns to middle BB
        
        Best for: Range-bound, sideways markets
        Weakness: Trending markets (false reversals)
        """


if __name__ == "__main__":
    # Example usage
    from ..data_provider import DataFetcher

    # Fetch sample data
    fetcher = DataFetcher()
    data = fetcher.fetch_stock_data(
        "AAPL", start_date="2022-01-01", end_date="2023-12-31"
    )

    # Create and run strategy
    strategy = MeanReversionStrategy()
    signals = strategy.generate_signals(data)

    print("Strategy Description:")
    print(strategy.get_strategy_description())

    print("\nFirst 10 signals:")
    print(signals.head(10))

    # Run backtest
    results = strategy.backtest(data)
    print("\nBacktest Results:")
    print(f"Total Return: {results['total_return']:.2%}")
    print(f"Final Capital: ${results['final_capital']:,.2f}")
