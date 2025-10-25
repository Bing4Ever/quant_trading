"""
Data Provider Module - 数据提供模块

纯粹的市场数据获取和管理接口，不包含业务数据存储。

组织结构：
- fetcher.py: DataFetcher - 从各种数据源获取市场数据
- manager.py: DataManager - 数据管理和缓存
"""

from .fetcher import DataFetcher
from .manager import DataManager

__all__ = [
    'DataFetcher',
    'DataManager',
]
