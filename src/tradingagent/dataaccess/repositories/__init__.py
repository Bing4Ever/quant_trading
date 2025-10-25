"""
Repositories - 数据仓储层

提供市场数据的访问接口
"""

from src.common.dataaccess import BaseRepository
from .market_data_repository import MarketDataRepository

__all__ = [
    'BaseRepository',
    'MarketDataRepository',
]
