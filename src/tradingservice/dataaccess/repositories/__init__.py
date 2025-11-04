"""
 Repositories - 数据仓储层

 提供业务数据的访问接口
"""

from src.common.dataaccess import BaseRepository
from .backtest_repository import BacktestRepository
from .optimization_repository import OptimizationRepository
from .favorite_repository import FavoriteRepository
from .strategy_comparison_repository import StrategyComparisonRepository
from .scheduler_execution_repository import SchedulerExecutionRepository

__all__ = [
    'BaseRepository',
    'BacktestRepository',
    'OptimizationRepository',
    'FavoriteRepository',
    'StrategyComparisonRepository',
    'SchedulerExecutionRepository',
]
