#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据提供器 - TradingAgent 数据访问统一接口

这是一个门面模式(Facade)类，封装了底层的数据获取、管理和存储功能。
外部代码应该通过这个接口访问数据，而不是直接使用底层模块。

架构：
    DataProvider (本文件) - 统一对外接口
      ↓ 内部使用
    data_provider/ 模块
      ├── fetcher.py - 实际数据获取
      ├── manager.py - 数据管理
      └── database.py - 数据存储
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import pandas as pd

# 导入内部实现
from .data_provider.fetcher import DataFetcher
from .data_provider.manager import DataManager


logger = logging.getLogger(__name__)


class DataProvider:
    """
    数据提供器 - TradingAgent 数据访问统一接口
    
    封装底层的 DataFetcher 和 DataManager，提供简洁的数据访问接口。
    """
    
    def __init__(self, provider: str = None):
        """
        初始化数据提供器
        
        Args:
            provider: 数据提供商 ('yfinance', 'alpha_vantage' 等)
        """
        self._fetcher = DataFetcher(provider=provider)
        self._manager = DataManager()
        logger.info("数据提供器初始化完成")
    
    def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        获取历史数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            interval: 数据间隔 (1d, 1h, 5m等)
            
        Returns:
            pd.DataFrame: 历史数据，包含Open/High/Low/Close/Volume列
        """
        # 委托给 DataFetcher
        return self._fetcher.fetch_stock_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
    
    def get_latest_data(
        self,
        symbol: str,
        days: int = 60,
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        获取最新数据
        
        Args:
            symbol: 股票代码
            days: 获取天数
            interval: 数据间隔
            
        Returns:
            pd.DataFrame: 最新数据
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return self.get_historical_data(
            symbol=symbol,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            interval=interval
        )
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        获取当前价格
        
        Args:
            symbol: 股票代码
            
        Returns:
            float: 当前价格
        """
        # 委托给 DataFetcher
        return self._fetcher.get_current_price(symbol)
    
    def get_batch_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        批量获取当前价格
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            Dict: 股票代码到价格的映射
        """
        prices = {}
        
        for symbol in symbols:
            price = self.get_current_price(symbol)
            if price:
                prices[symbol] = price
        
        logger.info(f"批量获取 {len(prices)}/{len(symbols)} 个股票价格")
        return prices
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取股票基本信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            Dict: 股票信息
        """
        # 委托给 DataFetcher
        return self._fetcher.get_stock_info(symbol)
    
    def clear_cache(self):
        """清空缓存"""
        # 委托给 DataFetcher
        self._fetcher.clear_cache()
        logger.info("数据缓存已清空")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict: 缓存统计
        """
        # 委托给 DataFetcher
        return self._fetcher.get_cache_stats()


class RealTimeDataProvider(DataProvider):
    """实时数据提供器（扩展类）"""
    
    def __init__(self, poll_interval: int = 1):
        """
        初始化实时数据提供器
        
        Args:
            poll_interval: 轮询间隔（秒）
        """
        super().__init__()
        self.poll_interval = poll_interval
        self.subscribed_symbols: set = set()
        logger.info(f"实时数据提供器初始化完成 (轮询间隔: {poll_interval}秒)")
    
    def subscribe(self, symbols: List[str]):
        """
        订阅股票实时数据
        
        Args:
            symbols: 股票代码列表
        """
        self.subscribed_symbols.update(symbols)
        logger.info(f"订阅实时数据: {symbols}")
    
    def unsubscribe(self, symbols: List[str]):
        """
        取消订阅
        
        Args:
            symbols: 股票代码列表
        """
        self.subscribed_symbols.difference_update(symbols)
        logger.info(f"取消订阅: {symbols}")
    
    def get_subscribed_prices(self) -> Dict[str, float]:
        """
        获取所有订阅股票的当前价格
        
        Returns:
            Dict: 股票代码到价格的映射
        """
        return self.get_batch_current_prices(list(self.subscribed_symbols))
