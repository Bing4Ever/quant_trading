"""
Backtesting Module

This module provides backtesting capabilities for trading strategies.

Classes:
    BacktestEngine: Core backtesting engine
    Trade: Individual trade representation
"""

from src.tradingagent.modules.backtesting.backtest_engine import BacktestEngine, Trade

__all__ = ["BacktestEngine", "Trade"]
