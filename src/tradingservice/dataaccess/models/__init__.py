"""
Data Models - 数据库模型

定义所有数据表的 ORM 模型
"""

from .backtest_result import BacktestResult
from .optimization_record import OptimizationRecord
from .favorite_stock import FavoriteStock
from .strategy_comparison import StrategyComparison
from .scheduler_execution import (
    AutomationTaskExecution,
    AutomationTaskOrder,
    AutomationRiskSnapshot,
)

__all__ = [
    'BacktestResult',
    'OptimizationRecord',
    'FavoriteStock',
    'StrategyComparison',
    'AutomationTaskExecution',
    'AutomationTaskOrder',
    'AutomationRiskSnapshot',
]
