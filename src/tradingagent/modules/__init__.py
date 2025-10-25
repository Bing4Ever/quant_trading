#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modules Package - 功能模块层

提供可插拔的业务逻辑模块：
- execution: 订单执行
- signal: 信号生成
- data: 数据获取
- risk: 风险控制
- strategies: 交易策略
- risk_management: 风险管理
"""

# 基础模块
from .execution import OrderExecutor
from .signal import SignalGenerator
from .data_provider import DataFetcher, DataManager

# 风险管理模块（从 risk_management 导入）
from .risk_management import RiskController, RiskLimits

# 策略和风险管理模块通过子包导入
# from .strategies import ...
# from .risk_management import ...

__all__ = [
    # 基础模块
    'OrderExecutor',
    'SignalGenerator',
    'DataFetcher',
    'DataManager',
    # 风险控制
    'RiskController',
    'RiskLimits',
    
    # 子包（通过 tradingagent.modules.strategies 访问）
    # 'strategies',
    # 'risk_management',
]
