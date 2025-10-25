"""
API Layer for Quantitative Trading System

This package provides RESTful API endpoints for:
- Task management and scheduling
- Strategy analysis and signal generation
- Portfolio management
- Backtesting operations
- Real-time data streaming via WebSocket

Main application located in: main.py
"""

__version__ = "1.0.0"

from .main import app

__all__ = ['app']
