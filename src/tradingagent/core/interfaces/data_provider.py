#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Provider Interface - 数据提供器接口定义

定义数据提供器的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List
import pandas as pd


class IDataProvider(ABC):
    """数据提供器接口"""
    
    @abstractmethod
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
            interval: 数据间隔
            
        Returns:
            pd.DataFrame: 历史数据
        """
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        获取当前价格
        
        Args:
            symbol: 股票代码
            
        Returns:
            float: 当前价格
        """
        pass
    
    @abstractmethod
    def get_batch_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        批量获取当前价格
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            Dict: 股票代码到价格的映射
        """
        pass
