"""
Data Update Model - 数据更新记录模型
"""

from sqlalchemy import Column, String, DateTime
from datetime import datetime
from src.common.dataaccess import OrmBase


class DataUpdate(OrmBase):
    """数据更新记录模型 - 跟踪每个股票的最后更新时间"""
    
    __tablename__ = 'data_updates'
    
    # 主键
    symbol = Column(String(20), primary_key=True, comment='股票代码')
    
    # 更新时间
    last_update = Column(DateTime, default=datetime.now, nullable=False, comment='最后更新时间')
    
    def __repr__(self):
        return f"<DataUpdate(symbol={self.symbol}, last_update={self.last_update})>"
