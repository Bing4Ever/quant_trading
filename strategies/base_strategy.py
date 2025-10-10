"""
Base strategy class for all trading strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from enum import Enum
import pandas as pd
import numpy as np

class SignalType(Enum):
    """Trading signal types."""

    BUY = 1
    SELL = -1
    HOLD = 0


class Position(Enum):
    """Position types."""

    LONG = 1
    SHORT = -1
    FLAT = 0


class BaseStrategy(ABC):
    """
    Base class for all trading strategies.

    All trading strategies should inherit from this class and implement
    the required abstract methods.
    """

    def __init__(self, name: str = None):
        """
        Initialize the strategy.

        Args:
            name: Strategy name
        """
        self.name = name or self.__class__.__name__
        self.parameters = {}
        self.signals = pd.DataFrame()
        self.positions = pd.DataFrame()
        self.trades = []
        self.performance_metrics = {}

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on market data.

        Args:
            data: Market data DataFrame with OHLCV columns

        Returns:
            DataFrame with trading signals
        """
        pass

    def set_parameters(self, **kwargs):
        """
        Set strategy parameters.

        Args:
            **kwargs: Parameter key-value pairs
        """
        self.parameters.update(kwargs)

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """
        Get strategy parameter value.

        Args:
            key: Parameter key
            default: Default value if key not found

        Returns:
            Parameter value
        """
        return self.parameters.get(key, default)

    def calculate_position_size(
        self,
        signal: float,
        price: float,
        account_value: float,
        risk_per_trade: float = 0.02,
    ) -> int:
        """
        Calculate position size based on risk management rules.

        Args:
            signal: Trading signal strength (-1 to 1)
            price: Current price
            account_value: Current account value
            risk_per_trade: Risk per trade as fraction of account value

        Returns:
            Position size in shares
        """
        if signal == 0:
            return 0

        # Basic position sizing: risk-based
        risk_amount = account_value * risk_per_trade
        position_value = risk_amount / abs(signal)
        position_size = int(position_value / price)

        return position_size if signal > 0 else -position_size

    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate input data format and completeness.

        Args:
            data: Market data DataFrame

        Returns:
            True if data is valid, False otherwise
        """
        required_columns = ["open", "high", "low", "close", "volume"]

        if data is None or data.empty:
            return False

        if not all(col in data.columns for col in required_columns):
            return False

        if data.isnull().any().any():
            return False

        return True

    def add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Add common technical indicators to the data.

        Args:
            data: Market data DataFrame

        Returns:
            DataFrame with added technical indicators
        """
        df = data.copy()

        # Simple Moving Averages
        df["sma_10"] = df["close"].rolling(window=10).mean()
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["sma_50"] = df["close"].rolling(window=50).mean()

        # Exponential Moving Averages
        df["ema_12"] = df["close"].ewm(span=12).mean()
        df["ema_26"] = df["close"].ewm(span=26).mean()

        # MACD
        df["macd"] = df["ema_12"] - df["ema_26"]
        df["macd_signal"] = df["macd"].ewm(span=9).mean()
        df["macd_histogram"] = df["macd"] - df["macd_signal"]

        # RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        df["bb_middle"] = df["close"].rolling(window=20).mean()
        bb_std = df["close"].rolling(window=20).std()
        df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
        df["bb_lower"] = df["bb_middle"] - (bb_std * 2)

        # Average True Range
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        df["atr"] = true_range.rolling(window=14).mean()

        return df

    def calculate_returns(self, prices: pd.Series) -> pd.Series:
        """
        Calculate returns from price series.

        Args:
            prices: Price series

        Returns:
            Returns series
        """
        return prices.pct_change().fillna(0)

    def calculate_volatility(self, returns: pd.Series, window: int = 30) -> pd.Series:
        """
        Calculate rolling volatility.

        Args:
            returns: Returns series
            window: Rolling window size

        Returns:
            Volatility series
        """
        return returns.rolling(window=window).std() * np.sqrt(252)  # Annualized

    def apply_stop_loss(
        self, data: pd.DataFrame, signals: pd.DataFrame, stop_loss_pct: float = 0.05
    ) -> pd.DataFrame:
        """
        Apply stop-loss rules to signals.

        Args:
            data: Market data
            signals: Trading signals
            stop_loss_pct: Stop-loss percentage

        Returns:
            Modified signals with stop-loss applied
        """
        modified_signals = signals.copy()

        # Implement stop-loss logic here
        # This is a simplified example
        for i in range(1, len(data)):
            if signals.iloc[i - 1]["signal"] != 0:  # If we have a position
                price_change = (
                    data.iloc[i]["close"] - data.iloc[i - 1]["close"]
                ) / data.iloc[i - 1]["close"]

                # Check for stop-loss
                if abs(price_change) > stop_loss_pct:
                    if (signals.iloc[i - 1]["signal"] > 0 and price_change < 0) or (
                        signals.iloc[i - 1]["signal"] < 0 and price_change > 0
                    ):
                        modified_signals.iloc[i]["signal"] = 0  # Close position

        return modified_signals

    def backtest(
        self,
        data: pd.DataFrame,
        initial_capital: float = 100000,
        commission: float = 0.001,
    ) -> Dict[str, Any]:
        """
        Simple backtest implementation.

        Args:
            data: Market data
            initial_capital: Starting capital
            commission: Commission rate per trade

        Returns:
            Backtest results
        """
        if not self.validate_data(data):
            raise ValueError("Invalid data format")

        # Generate signals
        signals = self.generate_signals(data)

        # Calculate performance
        capital = initial_capital
        positions = []
        portfolio_values = []

        for i, (date, row) in enumerate(data.iterrows()):
            if i < len(signals):
                signal = signals.iloc[i]["signal"] if "signal" in signals.columns else 0
                position_size = self.calculate_position_size(
                    signal, row["close"], capital
                )

                # Simple position tracking
                if position_size != 0:
                    trade_cost = abs(position_size * row["close"] * commission)
                    capital -= trade_cost

                positions.append(position_size)
                portfolio_values.append(capital)

        # Calculate performance metrics
        total_return = (capital - initial_capital) / initial_capital

        results = {
            "total_return": total_return,
            "final_capital": capital,
            "positions": positions,
            "portfolio_values": portfolio_values,
        }

        return results
