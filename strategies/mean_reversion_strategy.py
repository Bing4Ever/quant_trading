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

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate mean reversion signals based on Bollinger Bands and RSI.

        The strategy generates:
        - BUY signal when price touches lower Bollinger Band AND RSI < oversold
        - SELL signal when price touches upper Bollinger Band AND RSI > overbought
        - CLOSE signal when price returns to middle Bollinger Band

        Args:
            data: Market data DataFrame with OHLCV columns

        Returns:
            DataFrame with trading signals and indicators
        """
        if not self.validate_data(data):
            raise ValueError("Invalid data format")

        df = data.copy()

        # Get parameters
        bb_period = self.get_parameter("bb_period", 20)
        bb_std = self.get_parameter("bb_std", 2.0)
        rsi_period = self.get_parameter("rsi_period", 14)
        rsi_oversold = self.get_parameter("rsi_oversold", 30)
        rsi_overbought = self.get_parameter("rsi_overbought", 70)

        # Calculate Bollinger Bands
        df["bb_middle"] = df["close"].rolling(window=bb_period).mean()
        bb_rolling_std = df["close"].rolling(window=bb_period).std()
        df["bb_upper"] = df["bb_middle"] + (bb_rolling_std * bb_std)
        df["bb_lower"] = df["bb_middle"] - (bb_rolling_std * bb_std)

        # Calculate Bollinger Band position (0 = lower band, 1 = upper band)
        df["bb_position"] = (df["close"] - df["bb_lower"]) / (
            df["bb_upper"] - df["bb_lower"]
        )

        # Calculate RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        # Calculate additional indicators
        # Price distance from middle band
        df["price_deviation"] = (df["close"] - df["bb_middle"]) / df["bb_middle"] * 100

        # Bollinger Band width (volatility measure)
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"] * 100

        # Initialize signals
        df["signal"] = 0
        df["position"] = 0

        # Generate entry signals
        # Buy when price is near lower band AND RSI is oversold
        buy_condition = (
            (df["close"] <= df["bb_lower"] * 1.01)  # Within 1% of lower band
            & (df["rsi"] < rsi_oversold)
            & (df["bb_width"] > df["bb_width"].rolling(50).mean())  # Higher volatility
        )

        # Sell when price is near upper band AND RSI is overbought
        sell_condition = (
            (df["close"] >= df["bb_upper"] * 0.99)  # Within 1% of upper band
            & (df["rsi"] > rsi_overbought)
            & (df["bb_width"] > df["bb_width"].rolling(50).mean())  # Higher volatility
        )

        # Exit conditions
        # Exit long when price returns to middle band or RSI normalizes
        exit_long_condition = (df["close"] >= df["bb_middle"]) | (df["rsi"] >= 50)

        # Exit short when price returns to middle band or RSI normalizes
        exit_short_condition = (df["close"] <= df["bb_middle"]) | (df["rsi"] <= 50)

        # Apply signals
        current_position = 0
        positions = []
        signals = []

        for i in range(len(df)):
            signal = 0

            if current_position == 0:  # No position
                if buy_condition.iloc[i]:
                    signal = SignalType.BUY.value
                    current_position = 1
                elif sell_condition.iloc[i]:
                    signal = SignalType.SELL.value
                    current_position = -1

            elif current_position == 1:  # Long position
                if exit_long_condition.iloc[i] or sell_condition.iloc[i]:
                    signal = SignalType.SELL.value
                    current_position = 0

            elif current_position == -1:  # Short position
                if exit_short_condition.iloc[i] or buy_condition.iloc[i]:
                    signal = SignalType.BUY.value
                    current_position = 0

            signals.append(signal)
            positions.append(current_position)

        df["signal"] = signals
        df["position"] = positions

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

    def _calculate_signal_strength(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate signal strength based on how extreme the indicators are.

        Args:
            data: DataFrame with calculated indicators

        Returns:
            Series with signal strength values (0 to 1)
        """
        # RSI component
        rsi_strength = np.where(
            data["rsi"] < 30,
            (30 - data["rsi"]) / 30,  # Stronger when more oversold
            np.where(
                data["rsi"] > 70,
                (data["rsi"] - 70) / 30,  # Stronger when more overbought
                0,
            ),
        )

        # Bollinger Band component
        bb_strength = np.abs(data["bb_position"] - 0.5) * 2  # 0 at middle, 1 at bands

        # Combine components
        signal_strength = np.maximum(rsi_strength, bb_strength)

        return pd.Series(signal_strength, index=data.index)

    def add_volume_filter(
        self, data: pd.DataFrame, volume_ma_period: int = 20
    ) -> pd.DataFrame:
        """
        Add volume filter to improve signal quality.

        Only takes signals when volume is above average.

        Args:
            data: Market data with signals
            volume_ma_period: Period for volume moving average

        Returns:
            DataFrame with volume-filtered signals
        """
        df = data.copy()

        # Calculate volume moving average
        df["volume_ma"] = df["volume"].rolling(window=volume_ma_period).mean()
        df["volume_filter"] = df["volume"] > df["volume_ma"]

        # Apply volume filter to signals
        df.loc[~df["volume_filter"], "signal"] = 0

        return df

    def add_trend_filter(
        self, data: pd.DataFrame, trend_period: int = 50
    ) -> pd.DataFrame:
        """
        Add trend filter - avoid counter-trend trades in strong trends.

        Args:
            data: Market data with signals
            trend_period: Period for trend determination

        Returns:
            DataFrame with trend-filtered signals
        """
        df = data.copy()

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
        data: pd.DataFrame,
        bb_period_range: tuple = (10, 30),
        rsi_period_range: tuple = (10, 20),
        rsi_threshold_range: tuple = (20, 40),
    ) -> Dict[str, Any]:
        """
        Optimize strategy parameters.

        Args:
            data: Market data for optimization
            bb_period_range: Range for Bollinger Band period
            rsi_period_range: Range for RSI period
            rsi_threshold_range: Range for RSI thresholds

        Returns:
            Dictionary with best parameters and performance
        """
        best_params = {}
        best_return = -float("inf")
        results = []

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
                        backtest_results = self.backtest(data)
                        total_return = backtest_results["total_return"]

                        results.append(
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

                    except Exception as e:
                        print(f"Error optimizing parameters: {e}")
                        continue

        return {
            "best_parameters": best_params,
            "best_return": best_return,
            "all_results": results,
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
    from data import DataFetcher

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
    print(f"\nBacktest Results:")
    print(f"Total Return: {results['total_return']:.2%}")
    print(f"Final Capital: ${results['final_capital']:,.2f}")
