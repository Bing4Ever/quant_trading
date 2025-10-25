"""
Data Access Layer - 数据访问层

提供数据库操作的统一接口，包括：
- 基础设施：数据库引擎、ORM基类（来自 common）
- 数据模型：ORM模型定义
- 数据仓储：业务数据访问接口
"""

import logging
from pathlib import Path
from src.common.dataaccess import DatabaseEngine, OrmBase, BaseRepository
from .models import BacktestResult, OptimizationRecord, FavoriteStock, StrategyComparison
from .repositories import (
    BacktestRepository,
    OptimizationRepository,
    FavoriteRepository,
    StrategyComparisonRepository
)

logger = logging.getLogger(__name__)

# 数据库引擎单例
_engines = {}


def get_engine(db_name: str = 'business', db_type: str = 'business', echo: bool = False) -> DatabaseEngine:
    """
    获取数据库引擎（单例模式）
    
    Args:
        db_name: 数据库文件名（business, cache等）
        db_type: 数据库类型（business或cache），决定存放目录
        echo: 是否打印SQL日志
        
    Returns:
        DatabaseEngine 实例
    """
    if db_name not in _engines:
        # 数据库文件路径：db/{db_type}/{db_name}.db
        db_path = Path(__file__).parent / 'db' / db_type / f'{db_name}.db'
        
        # 转换为 SQLAlchemy URL 格式
        db_url = f'sqlite:///{db_path.as_posix()}'
        
        # 创建引擎
        engine = DatabaseEngine(db_url, echo=echo)
        
        # 创建所有表
        engine.create_tables(OrmBase)
        
        _engines[db_name] = engine
        logger.info(f"数据库引擎已创建: {db_type}/{db_name}.db")
    
    return _engines[db_name]


def get_backtest_repository() -> BacktestRepository:
    """
    获取回测仓储（便捷方法）
    
    Returns:
        BacktestRepository 实例
    """
    engine = get_engine('business', 'business')
    session = engine.get_session()
    return BacktestRepository(session)


def get_optimization_repository() -> OptimizationRepository:
    """
    获取优化仓储（便捷方法）
    
    Returns:
        OptimizationRepository 实例
    """
    engine = get_engine('business', 'business')
    session = engine.get_session()
    return OptimizationRepository(session)


def get_favorite_repository() -> FavoriteRepository:
    """
    获取收藏仓储（便捷方法）
    
    Returns:
        FavoriteRepository 实例
    """
    engine = get_engine('business', 'business')
    session = engine.get_session()
    return FavoriteRepository(session)


def get_strategy_comparison_repository() -> StrategyComparisonRepository:
    """
    获取策略对比仓储（便捷方法）
    
    Returns:
        StrategyComparisonRepository 实例
    """
    engine = get_engine('business', 'business')
    session = engine.get_session()
    return StrategyComparisonRepository(session)


__all__ = [
    # 基础设施
    'DatabaseEngine',
    'OrmBase',
    # 模型
    'BacktestResult',
    'OptimizationRecord',
    'FavoriteStock',
    'StrategyComparison',
    # 仓储
    'BaseRepository',
    'BacktestRepository',
    'OptimizationRepository',
    'FavoriteRepository',
    'StrategyComparisonRepository',
    # 便捷函数
    'get_engine',
    'get_backtest_repository',
    'get_optimization_repository',
    'get_favorite_repository',
    'get_strategy_comparison_repository',
]
