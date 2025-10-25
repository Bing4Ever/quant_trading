"""
Market Data Repository - 市场数据仓储

管理市场数据缓存的存储和检索
"""

import pandas as pd
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy import and_
from src.common.dataaccess import BaseRepository
from ..models.stock_data import StockData
from ..models.data_update import DataUpdate


class MarketDataRepository(BaseRepository[StockData]):
    """市场数据仓储 - 管理股票行情数据缓存"""
    
    def __init__(self, session=None):
        super().__init__(StockData, session)
    
    def save_stock_data(self, symbol: str, data: pd.DataFrame):
        """
        保存股票数据（批量插入）
        
        Args:
            symbol: 股票代码
            data: DataFrame，包含 date, open, high, low, close, volume, adjusted_close
        """
        # 准备数据
        records = []
        for date, row in data.iterrows():
            stock_data = StockData(
                symbol=symbol,
                date=date.date() if isinstance(date, pd.Timestamp) else date,
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']),
                adjusted_close=float(row.get('Adj Close', row['Close']))
            )
            records.append(stock_data)
        
        # 批量插入（使用 merge 避免重复）
        for record in records:
            self.session.merge(record)
        
        self.session.commit()
    
    def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        获取股票数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame，包含 OHLCV 数据
        """
        query = self.session.query(StockData).filter(StockData.symbol == symbol)
        
        if start_date:
            query = query.filter(StockData.date >= start_date.date())
        
        if end_date:
            query = query.filter(StockData.date <= end_date.date())
        
        query = query.order_by(StockData.date)
        
        results = query.all()
        
        if not results:
            return pd.DataFrame()
        
        # 转换为 DataFrame
        data = {
            'Open': [r.open for r in results],
            'High': [r.high for r in results],
            'Low': [r.low for r in results],
            'Close': [r.close for r in results],
            'Volume': [r.volume for r in results],
            'Adj Close': [r.adjusted_close for r in results],
        }
        
        df = pd.DataFrame(data, index=[r.date for r in results])
        df.index.name = 'Date'
        
        return df
    
    def needs_update(self, symbol: str, end_date: Optional[datetime] = None) -> bool:
        """
        检查是否需要更新数据
        
        Args:
            symbol: 股票代码
            end_date: 结束日期（默认为当前时间）
            
        Returns:
            True 如果需要更新
        """
        if end_date is None:
            end_date = datetime.now()
        
        # 查询最后更新时间
        update_record = self.session.query(DataUpdate).filter(
            DataUpdate.symbol == symbol
        ).first()
        
        if update_record is None:
            return True
        
        # 如果数据超过 1 天，需要更新
        return (end_date - update_record.last_update).days > 1
    
    def update_timestamp(self, symbol: str):
        """
        更新数据时间戳
        
        Args:
            symbol: 股票代码
        """
        update_record = self.session.query(DataUpdate).filter(
            DataUpdate.symbol == symbol
        ).first()
        
        if update_record:
            update_record.last_update = datetime.now()
        else:
            update_record = DataUpdate(symbol=symbol, last_update=datetime.now())
            self.session.add(update_record)
        
        self.session.commit()
    
    def get_cached_symbols(self) -> List[str]:
        """
        获取所有已缓存的股票代码
        
        Returns:
            股票代码列表
        """
        results = self.session.query(StockData.symbol).distinct().all()
        return [r[0] for r in results]
    
    def delete_old_data(self, symbol: str, days: int = 365):
        """
        删除旧数据（保留最近 N 天）
        
        Args:
            symbol: 股票代码
            days: 保留天数
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        self.session.query(StockData).filter(
            and_(
                StockData.symbol == symbol,
                StockData.date < cutoff_date.date()
            )
        ).delete()
        
        self.session.commit()
