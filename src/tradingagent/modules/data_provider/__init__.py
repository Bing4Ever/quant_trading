#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Provider Module - 行情数据统一入口

子模块：
- data_fetcher.py: DataFetcher - 连接外部数据源抓取行情
- data_manager.py: DataManager - 本地缓存/数据库管理
- data_provider.py: DataProvider / RealTimeDataProvider - 对外暴露的统一接口
"""

from .data_fetcher import DataFetcher
from .data_manager import DataManager
from .data_provider import DataProvider, RealTimeDataProvider

__all__ = [
    'DataFetcher',
    'DataManager',
    'DataProvider',
    'RealTimeDataProvider',
]
