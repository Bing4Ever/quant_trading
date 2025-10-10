"""
Comprehensive backtesting engine for trading strategies.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import warnings
from config import config


class Trade:
    """Represents a single trade."""
    
    def __init__(
        self,
        symbol: str,
        entry_date: datetime,
        entry_price: float,
        quantity: int,
        trade_type: str = 'long'
    ):
        self.symbol = symbol
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.quantity = quantity
        self.trade_type = trade_type  # 'long' or 'short'
        
        # Exit information (filled when trade is closed)
        self.exit_date = None
        self.exit_price = None
        self.pnl = 0.0
        self.return_pct = 0.0
        self.commission = 0.0
        self.is_open = True
    
    def close_trade(self, exit_date: datetime, exit_price: float, commission: float = 0.0):
        """Close the trade and calculate P&L."""
        self.exit_date = exit_date
        self.exit_price = exit_price
        self.commission = commission
        self.is_open = False
        
        if self.trade_type == 'long':
            self.pnl = (exit_price - self.entry_price) * self.quantity - commission
            self.return_pct = (exit_price - self.entry_price) / self.entry_price
        else:  # short
            self.pnl = (self.entry_price - exit_price) * self.quantity - commission
            self.return_pct = (self.entry_price - exit_price) / self.entry_price
    
    def get_unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L for open trades."""
        if not self.is_open:
            return self.pnl
        
        if self.trade_type == 'long':
            return (current_price - self.entry_price) * self.quantity
        else:  # short
            return (self.entry_price - current_price) * self.quantity


class BacktestEngine:
    """
    Comprehensive backtesting engine for trading strategies.
    """
    
    def __init__(
        self,
        initial_capital: float = None,
        commission: float = None,
        slippage: float = None,
        margin_requirement: float = 1.0
    ):
        """
        Initialize backtesting engine.
        
        Args:
            initial_capital: Starting capital
            commission: Commission per trade (as fraction of trade value)
            slippage: Slippage per trade (as fraction of price)
            margin_requirement: Margin requirement for trades (1.0 = no margin)
        """
        # Get default values from config
        trading_config = config.get('trading', {})
        
        self.initial_capital = initial_capital or trading_config.get('initial_capital', 100000)
        self.commission = commission or trading_config.get('commission', 0.001)
        self.slippage = slippage or trading_config.get('slippage', 0.0005)
        self.margin_requirement = margin_requirement
        
        # State variables
        self.current_capital = self.initial_capital
        self.positions = {}  # symbol -> quantity
        self.trades = []  # List of Trade objects
        self.portfolio_values = []
        self.portfolio_returns = []
        self.benchmark_returns = []
        
        # Performance tracking
        self.daily_pnl = []
        self.daily_returns = []
        self.drawdowns = []
        
    def run_backtest(
        self,
        strategy,
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
        start_date: str = None,
        end_date: str = None,
        benchmark_data: pd.DataFrame = None
    ) -> Dict[str, Any]:
        """
        Run backtest for a given strategy.
        
        Args:
            strategy: Trading strategy instance
            data: Market data (DataFrame for single asset, Dict for multiple assets)
            start_date: Backtest start date
            end_date: Backtest end date
            benchmark_data: Benchmark data for comparison
            
        Returns:
            Dictionary with backtest results
        """
        self._reset_state()
        
        # Handle single asset vs multi-asset data
        if isinstance(data, pd.DataFrame):
            # Single asset
            symbols = ['SINGLE_ASSET']
            data_dict = {'SINGLE_ASSET': data}
        else:
            # Multiple assets
            symbols = list(data.keys())
            data_dict = data
        
        # Filter data by date range
        if start_date or end_date:
            filtered_data = {}
            for symbol, df in data_dict.items():
                filtered_df = df.copy()
                if start_date:
                    filtered_df = filtered_df[filtered_df.index >= start_date]
                if end_date:
                    filtered_df = filtered_df[filtered_df.index <= end_date]
                filtered_data[symbol] = filtered_df
            data_dict = filtered_data
        
        # Get all unique dates and sort
        all_dates = set()
        for df in data_dict.values():
            all_dates.update(df.index)
        all_dates = sorted(list(all_dates))
        
        if not all_dates:
            raise ValueError("No data available for backtesting")
        
        # Generate signals for each asset
        signals_dict = {}
        for symbol, df in data_dict.items():
            try:
                signals = strategy.generate_signals(df)
                signals_dict[symbol] = signals
            except Exception as e:
                warnings.warn(f"Error generating signals for {symbol}: {e}")
                continue
        
        # Run simulation day by day
        for date in all_dates:
            self._process_day(date, data_dict, signals_dict, symbols)
        
        # Close any remaining open positions
        self._close_all_positions(all_dates[-1], data_dict)
        
        # Calculate performance metrics
        results = self._calculate_performance_metrics(benchmark_data)
        
        return results
    
    def _reset_state(self):
        """Reset engine state for new backtest."""
        self.current_capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.portfolio_values = []
        self.portfolio_returns = []
        self.benchmark_returns = []
        self.daily_pnl = []
        self.daily_returns = []
        self.drawdowns = []
    
    def _process_day(
        self,
        date: datetime,
        data_dict: Dict[str, pd.DataFrame],
        signals_dict: Dict[str, pd.DataFrame],
        symbols: List[str]
    ):
        """Process a single trading day."""
        day_start_capital = self.current_capital
        
        # Process each symbol
        for symbol in symbols:
            if symbol not in data_dict or symbol not in signals_dict:
                continue
            
            df = data_dict[symbol]
            signals = signals_dict[symbol]
            
            # Check if we have data for this date
            if date not in df.index:
                continue
            
            price_data = df.loc[date]
            
            # Find corresponding signal
            signal_idx = None
            for i, signal_date in enumerate(signals.index):
                if signal_date <= date:
                    signal_idx = i
                else:
                    break
            
            if signal_idx is None:
                continue
            
            signal_data = signals.iloc[signal_idx]
            signal = signal_data.get('signal', 0)
            
            if signal != 0:
                self._execute_trade(symbol, date, price_data, signal)
        
        # Calculate portfolio value
        portfolio_value = self._calculate_portfolio_value(date, data_dict)
        self.portfolio_values.append({
            'date': date,
            'value': portfolio_value,
            'cash': self.current_capital,
            'positions_value': portfolio_value - self.current_capital
        })
        
        # Calculate daily return
        if len(self.portfolio_values) > 1:
            prev_value = self.portfolio_values[-2]['value']
            daily_return = (portfolio_value - prev_value) / prev_value
            self.daily_returns.append(daily_return)
        else:
            self.daily_returns.append(0.0)
    
    def _execute_trade(
        self,
        symbol: str,
        date: datetime,
        price_data: pd.Series,
        signal: float
    ):
        """Execute a trade based on signal."""
        price = price_data['close']
        
        # Apply slippage
        if signal > 0:  # Buy
            execution_price = price * (1 + self.slippage)
        else:  # Sell
            execution_price = price * (1 - self.slippage)
        
        # Calculate position size
        position_value = abs(signal) * self.current_capital * 0.1  # 10% max position
        quantity = int(position_value / execution_price)
        
        if quantity == 0:
            return
        
        # Calculate commission
        trade_value = quantity * execution_price
        commission = trade_value * self.commission
        
        current_position = self.positions.get(symbol, 0)
        
        if signal > 0:  # Buy signal
            if current_position <= 0:  # Open long or close short
                if current_position < 0:
                    # Close short position first
                    self._close_position(symbol, date, execution_price, commission / 2)
                
                # Open long position
                if self.current_capital >= trade_value + commission:
                    self.current_capital -= (trade_value + commission)
                    self.positions[symbol] = quantity
                    
                    trade = Trade(symbol, date, execution_price, quantity, 'long')
                    self.trades.append(trade)
        
        else:  # Sell signal (signal < 0)
            if current_position >= 0:  # Close long or open short
                if current_position > 0:
                    # Close long position
                    self._close_position(symbol, date, execution_price, commission / 2)
                
                # For simplicity, we'll just close positions rather than short
                # In a full implementation, you would handle short selling here
    
    def _close_position(
        self,
        symbol: str,
        date: datetime,
        price: float,
        commission: float
    ):
        """Close an existing position."""
        if symbol not in self.positions or self.positions[symbol] == 0:
            return
        
        quantity = self.positions[symbol]
        trade_value = abs(quantity) * price
        
        # Find the corresponding open trade
        for trade in reversed(self.trades):
            if trade.symbol == symbol and trade.is_open:
                trade.close_trade(date, price, commission)
                self.current_capital += trade_value - commission
                break
        
        # Remove position
        self.positions[symbol] = 0
    
    def _close_all_positions(self, final_date: datetime, data_dict: Dict[str, pd.DataFrame]):
        """Close all open positions at the end of backtesting."""
        for symbol, quantity in self.positions.items():
            if quantity != 0 and symbol in data_dict:
                df = data_dict[symbol]
                if final_date in df.index:
                    final_price = df.loc[final_date, 'close']
                    self._close_position(symbol, final_date, final_price, 0)
    
    def _calculate_portfolio_value(
        self,
        date: datetime,
        data_dict: Dict[str, pd.DataFrame]
    ) -> float:
        """Calculate total portfolio value."""
        total_value = self.current_capital
        
        for symbol, quantity in self.positions.items():
            if quantity != 0 and symbol in data_dict:
                df = data_dict[symbol]
                if date in df.index:
                    current_price = df.loc[date, 'close']
                    position_value = quantity * current_price
                    total_value += position_value
        
        return total_value
    
    def _calculate_performance_metrics(self, benchmark_data: pd.DataFrame = None) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        if not self.portfolio_values:
            return {}
        
        # Convert to DataFrame
        portfolio_df = pd.DataFrame(self.portfolio_values)
        portfolio_df.set_index('date', inplace=True)
        
        # Calculate returns
        portfolio_returns = portfolio_df['value'].pct_change().fillna(0)
        
        # Basic metrics
        total_return = (portfolio_df['value'].iloc[-1] - self.initial_capital) / self.initial_capital
        annual_return = (1 + total_return) ** (252 / len(portfolio_df)) - 1
        volatility = portfolio_returns.std() * np.sqrt(252)
        
        # Risk metrics
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # Drawdown calculation
        running_max = portfolio_df['value'].expanding().max()
        drawdown = (portfolio_df['value'] - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Trade statistics
        completed_trades = [t for t in self.trades if not t.is_open]
        winning_trades = [t for t in completed_trades if t.pnl > 0]
        losing_trades = [t for t in completed_trades if t.pnl < 0]
        
        win_rate = len(winning_trades) / len(completed_trades) if completed_trades else 0
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        results = {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_trades': len(completed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'final_capital': portfolio_df['value'].iloc[-1],
            'portfolio_values': portfolio_df,
            'trades': completed_trades,
            'daily_returns': portfolio_returns
        }
        
        # Benchmark comparison if provided
        if benchmark_data is not None:
            benchmark_returns = benchmark_data['close'].pct_change().fillna(0)
            benchmark_total_return = (benchmark_data['close'].iloc[-1] - benchmark_data['close'].iloc[0]) / benchmark_data['close'].iloc[0]
            
            # Calculate alpha and beta
            portfolio_returns_aligned = portfolio_returns.reindex(benchmark_returns.index).fillna(0)
            covariance = np.cov(portfolio_returns_aligned, benchmark_returns)[0, 1]
            benchmark_variance = np.var(benchmark_returns)
            beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
            
            risk_free_rate = config.get('backtesting.risk_free_rate', 0.02) / 252  # Daily
            alpha = annual_return - (risk_free_rate * 252 + beta * (benchmark_returns.mean() * 252 - risk_free_rate * 252))
            
            results.update({
                'benchmark_return': benchmark_total_return,
                'alpha': alpha,
                'beta': beta,
                'information_ratio': (annual_return - benchmark_returns.mean() * 252) / (portfolio_returns - benchmark_returns).std() * np.sqrt(252) if (portfolio_returns - benchmark_returns).std() > 0 else 0
            })
        
        return results