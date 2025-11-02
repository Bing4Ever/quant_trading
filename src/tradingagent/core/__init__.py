#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Package - 核心层

包含接口定义、数据模型和基础实现。
"""

# Models
from .models import (
    OrderType,
    OrderSide,
    OrderStatus,
    TradingMode,
    Order,
    Position,
    TradingSignal,
    Balance,
    Account,
)

# Interfaces
from .interfaces import IBroker, IDataProvider, IRiskController

# Brokers
from .brokers import (
    BrokerFactory,
    SimulationBroker,
    AlpacaBroker,
    YFinanceBroker,
    AlphaVantageBroker,
)

# Core utilities
from .indicators import TechnicalIndicators
from .risk import RiskMetrics
from .data import DataUtils

__all__ = [
    # Enums
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "TradingMode",
    # Models
    "Order",
    "Position",
    "TradingSignal",
    "Balance",
    "Account",
    # Interfaces
    "IBroker",
    "IDataProvider",
    "IRiskController",
    # Brokers
    "SimulationBroker",
    "AlpacaBroker",
    "YFinanceBroker",
    "AlphaVantageBroker",
    "BrokerFactory",
    # Core utilities
    "TechnicalIndicators",
    "RiskMetrics",
    "DataUtils",
]
