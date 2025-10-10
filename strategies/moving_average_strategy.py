"""
Moving Average Crossover Strategy.

A classic trend-following strategy that generates buy signals when a short-term
moving average crosses above a long-term moving average, and sell signals when
the opposite occurs.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy, SignalType


class MovingAverageStrategy(BaseStrategy):
    """
    Moving Average Crossover Strategy.
    
    Parameters:
    -----------
    short_window : int
        Period for short-term moving average (default: 20)
    long_window : int
        Period for long-term moving average (default: 50)
    ma_type : str
        Type of moving average ('sma' or 'ema', default: 'sma')
    """
    
    def __init__(self, short_window: int = 20, long_window: int = 50, ma_type: str = 'sma'):
        """
        Initialize Moving Average Strategy.
        
        Args:
            short_window: Short-term moving average period
            long_window: Long-term moving average period  
            ma_type: Type of moving average ('sma' or 'ema')
        """
        super().__init__("Moving Average Crossover")
        
        self.set_parameters(
            short_window=short_window,
            long_window=long_window,
            ma_type=ma_type
        )
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on moving average crossover.
        
        The strategy generates:
        - BUY signal when short MA crosses above long MA
        - SELL signal when short MA crosses below long MA
        - HOLD signal otherwise
        
        Args:
            data: Market data DataFrame with OHLCV columns
            
        Returns:
            DataFrame with trading signals and moving averages
        """
        if not self.validate_data(data):
            raise ValueError("Invalid data format")
        
        df = data.copy()
        
        short_window = self.get_parameter('short_window', 20)
        long_window = self.get_parameter('long_window', 50)
        ma_type = self.get_parameter('ma_type', 'sma')
        
        # Calculate moving averages
        if ma_type == 'sma':
            df['short_ma'] = df['close'].rolling(window=short_window).mean()
            df['long_ma'] = df['close'].rolling(window=long_window).mean()
        elif ma_type == 'ema':
            df['short_ma'] = df['close'].ewm(span=short_window).mean()
            df['long_ma'] = df['close'].ewm(span=long_window).mean()
        else:
            raise ValueError(f"Invalid ma_type: {ma_type}")
        
        # Generate signals
        df['signal'] = 0
        df['position'] = 0
        
        # Create crossover signals
        df['crossover'] = np.where(
            (df['short_ma'] > df['long_ma']) & 
            (df['short_ma'].shift(1) <= df['long_ma'].shift(1)),
            1, 0
        )
        
        df['crossunder'] = np.where(
            (df['short_ma'] < df['long_ma']) & 
            (df['short_ma'].shift(1) >= df['long_ma'].shift(1)),
            1, 0
        )
        
        # Set signals
        df.loc[df['crossover'] == 1, 'signal'] = SignalType.BUY.value
        df.loc[df['crossunder'] == 1, 'signal'] = SignalType.SELL.value
        
        # Calculate position (1 for long, -1 for short, 0 for flat)
        current_position = 0
        positions = []
        
        for i, row in df.iterrows():
            if row['signal'] == SignalType.BUY.value:
                current_position = 1
            elif row['signal'] == SignalType.SELL.value:
                current_position = 0  # or -1 for short selling
            
            positions.append(current_position)
        
        df['position'] = positions
        
        # Add additional metrics
        df['ma_spread'] = df['short_ma'] - df['long_ma']
        df['ma_spread_pct'] = (df['short_ma'] - df['long_ma']) / df['long_ma'] * 100
        
        # Store signals for later use
        self.signals = df[['close', 'short_ma', 'long_ma', 'signal', 'position', 'ma_spread']].copy()
        
        return df[['signal', 'position', 'short_ma', 'long_ma', 'ma_spread']]
    
    def add_trend_filter(self, data: pd.DataFrame, trend_window: int = 200) -> pd.DataFrame:
        """
        Add a trend filter to improve signal quality.
        
        Only takes long positions when price is above long-term trend.
        
        Args:
            data: Market data with signals
            trend_window: Period for trend filter moving average
            
        Returns:
            DataFrame with filtered signals
        """
        df = data.copy()
        
        # Calculate trend filter
        df['trend_ma'] = df['close'].rolling(window=trend_window).mean()
        df['trend_filter'] = df['close'] > df['trend_ma']
        
        # Apply filter to signals
        original_signals = df['signal'].copy()
        
        # Only allow buy signals when above trend
        df.loc[(df['signal'] == SignalType.BUY.value) & (~df['trend_filter']), 'signal'] = 0
        
        # Force sell when trend turns down
        df.loc[(df['position'].shift(1) == 1) & (~df['trend_filter']), 'signal'] = SignalType.SELL.value
        
        return df
    
    def optimize_parameters(
        self, 
        data: pd.DataFrame, 
        short_range: tuple = (5, 50),
        long_range: tuple = (20, 200),
        step: int = 5
    ) -> Dict[str, Any]:
        """
        Optimize strategy parameters using grid search.
        
        Args:
            data: Market data for optimization
            short_range: Range for short window (min, max)
            long_range: Range for long window (min, max)
            step: Step size for parameter search
            
        Returns:
            Dictionary with best parameters and performance metrics
        """
        best_params = {}
        best_return = -float('inf')
        results = []
        
        for short_window in range(short_range[0], short_range[1] + 1, step):
            for long_window in range(long_range[0], long_range[1] + 1, step):
                if short_window >= long_window:
                    continue
                
                # Set parameters
                self.set_parameters(short_window=short_window, long_window=long_window)
                
                try:
                    # Run backtest
                    backtest_results = self.backtest(data)
                    total_return = backtest_results['total_return']
                    
                    results.append({
                        'short_window': short_window,
                        'long_window': long_window,
                        'total_return': total_return
                    })
                    
                    if total_return > best_return:
                        best_return = total_return
                        best_params = {
                            'short_window': short_window,
                            'long_window': long_window
                        }
                
                except Exception as e:
                    print(f"Error optimizing parameters {short_window}, {long_window}: {e}")
                    continue
        
        return {
            'best_parameters': best_params,
            'best_return': best_return,
            'all_results': results
        }
    
    def get_strategy_description(self) -> str:
        """Get strategy description."""
        short_window = self.get_parameter('short_window', 20)
        long_window = self.get_parameter('long_window', 50)
        ma_type = self.get_parameter('ma_type', 'sma')
        
        return f"""
        Moving Average Crossover Strategy
        ================================
        
        Type: Trend Following
        Short MA: {short_window} periods ({ma_type.upper()})
        Long MA: {long_window} periods ({ma_type.upper()})
        
        Rules:
        - BUY when short MA crosses above long MA
        - SELL when short MA crosses below long MA
        
        Best for: Trending markets
        Weakness: Whipsaws in sideways markets
        """


if __name__ == "__main__":
    # Example usage
    from data import DataFetcher
    
    # Fetch sample data
    fetcher = DataFetcher()
    data = fetcher.fetch_stock_data('AAPL', start_date='2022-01-01', end_date='2023-12-31')
    
    # Create and run strategy
    strategy = MovingAverageStrategy(short_window=20, long_window=50)
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