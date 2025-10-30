#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingAgent Package - 底层可执行逻辑模块

架构层次：
- core.interfaces: 接口定义
- core.models: 数据模型  
- core.brokers: 券商实现
- modules: 功能模块（execution, signal, data, risk, strategies, risk_management）
"""

# 从 core 导入（保持向后兼容的导出名称）
from .core import (
    # Enums
    OrderType,
    OrderSide,
    OrderStatus,
    TradingMode,
    
    # Models
    Order,
    Position,
    TradingSignal,
    Balance,
    Account,
    
    # Interfaces
    IBroker,
    IDataProvider,
    IRiskController,
    
    # Brokers
    SimulationBroker,
    AlpacaBroker,
    BrokerFactory,
)

# 从 modules 导入基础模块
from .modules import (
    OrderExecutor,
    SignalGenerator,
    DataFetcher,
    DataManager,
    RiskController,
    RiskLimits
)

# 从 modules.strategies 导入
from .modules.strategies import (
    BaseStrategy,
    MovingAverageStrategy,
    RSIStrategy,
    BollingerBandsStrategy,
    MeanReversionStrategy,
    MultiStrategyRunner,
)

# 从 modules.risk_management 导入
from .modules.risk_management import (
    RiskManager,
    RiskMonitor,
    RiskCalculator,
    PositionLimits as RMPositionLimits,
    RiskMetrics,
)

# 从 modules.backtesting 导入
from .modules.backtesting import (
    BacktestEngine,
    Trade,
)

# 向后兼容：提供旧的名称
BrokerInterface = IBroker

__version__ = "2.0.0"

__all__ = [
    # Enums
    'OrderType',
    'OrderSide',
    'OrderStatus',
    'TradingMode',
    
    # Models
    'Order',
    'Position',
    'TradingSignal',
    'Balance',
    'Account',
    
    # Interfaces (同时导出新旧名称)
    'IBroker',
    'BrokerInterface',  # 向后兼容
    'IDataProvider',
    'IRiskController',
    
    # Implementations
    'SimulationBroker',
    'AlpacaBroker',
    'BrokerFactory',
    
    # Basic Modules
    'OrderExecutor',
    'SignalGenerator',
    'DataFetcher',
    'DataManager',
    'RiskController',
    'RiskLimits',
    
    # Strategies
    'BaseStrategy',
    'MovingAverageStrategy',
    'RSIStrategy',
    'BollingerBandsStrategy',
    'MeanReversionStrategy',
    'MultiStrategyRunner',
    
    # Risk Management
    'RiskManager',
    'RiskMonitor',
    'RiskCalculator',
    'RMPositionLimits',
    'RiskMetrics',
    
    # Backtesting
    'BacktestEngine',
    'Trade',
]

