"""
Stock Data Model - 股票行情数据模型
"""

from sqlalchemy import Column, String, Date, Float, Integer
from src.common.dataaccess import OrmBase


class StockData(OrmBase):
    """股票行情数据模型 - 缓存从外部 API 获取的 OHLCV 数据"""
    
    __tablename__ = 'stock_data'
    
    # 联合主键
    symbol = Column(String(20), primary_key=True, comment='股票代码')
    date = Column(Date, primary_key=True, comment='日期')
    
    # OHLCV 数据
    open = Column(Float, nullable=False, comment='开盘价')
    high = Column(Float, nullable=False, comment='最高价')
    low = Column(Float, nullable=False, comment='最低价')
    close = Column(Float, nullable=False, comment='收盘价')
    volume = Column(Integer, nullable=False, comment='成交量')
    adjusted_close = Column(Float, comment='复权收盘价')
    
    def __repr__(self):
        return f"<StockData(symbol={self.symbol}, date={self.date}, close={self.close})>"
