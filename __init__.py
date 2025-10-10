"""
Quantitative Trading System
==========================

A comprehensive Python-based quantitative trading framework for strategy development,
backtesting, risk management, and portfolio optimization.

Modules:
--------
- data: Market data fetching and management
- strategies: Trading strategy implementations  
- backtesting: Strategy backtesting framework
- risk_management: Risk assessment and management
- portfolio: Portfolio optimization and management
- utils: Utility functions and helpers
"""

__version__ = "1.0.0"
__author__ = "Quantitative Trading Team"

# Import main modules for easy access
from . import data
from . import strategies
from . import backtesting
from . import risk_management
from . import portfolio
from . import utils