"""
Data Access Layer - 市场数据访问层

提供市场数据缓存的统一接口
"""

import logging
from pathlib import Path
from src.common.dataaccess import DatabaseEngine, OrmBase, BaseRepository
from .models import StockData, DataUpdate
from .repositories import MarketDataRepository

logger = logging.getLogger(__name__)

# 数据库引擎单例
_engine = None


def get_engine(db_path: str = None, echo: bool = False) -> DatabaseEngine:
    """
    获取数据库引擎（单例模式）

    Args:
        db_path: 数据库文件路径（默认为 db/market_data.db）
        echo: 是否打印 SQL 日志

    Returns:
        DatabaseEngine 实例
    """
    global _engine

    if _engine is None:
        # 默认数据库路径
        if db_path is None:
            db_path = Path(__file__).parent / "db" / "market_data.db"

        # 创建引擎
        db_url = f"sqlite:///{db_path}"
        _engine = DatabaseEngine(db_url, echo=echo)

        # 创建所有表
        _engine.create_tables(OrmBase)

        logger.info(f"市场数据库引擎已创建: {db_path}")

    return _engine


def get_market_data_repository() -> MarketDataRepository:
    """
    获取市场数据仓储（便捷方法）

    Returns:
        MarketDataRepository 实例
    """
    engine = get_engine()
    session = engine.get_session()
    return MarketDataRepository(session)


__all__ = [
    # 基础设施
    "DatabaseEngine",
    "OrmBase",
    # 模型
    "StockData",
    "DataUpdate",
    # 仓储
    "BaseRepository",
    "MarketDataRepository",
    # 便捷函数
    "get_engine",
    "get_market_data_repository",
]
