"""
Common Data Access Layer - 公共数据访问层

提供所有数据访问的基础设施：
- OrmBase: SQLAlchemy 声明式基类
- DatabaseEngine: 数据库引擎管理
- BaseRepository: 通用仓储基类

使用方式：
    from src.common.dataaccess import OrmBase, DatabaseEngine, BaseRepository
"""

from .orm_base import OrmBase
from .database_engine import DatabaseEngine
from .base_repository import BaseRepository

__all__ = [
    'OrmBase',
    'DatabaseEngine',
    'BaseRepository',
]
