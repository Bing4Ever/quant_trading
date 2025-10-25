"""
Favorite Stock Model - 收藏股票模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from datetime import datetime
from src.common.dataaccess import OrmBase


class FavoriteStock(OrmBase):
    """收藏股票模型"""
    
    __tablename__ = 'favorite_stocks'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 股票信息
    symbol = Column(String(20), unique=True, nullable=False, index=True, comment='股票代码')
    name = Column(String(100), comment='股票名称')
    sector = Column(String(100), comment='所属板块')
    
    # 关联信息
    last_backtest_id = Column(Integer, ForeignKey('backtest_results.id'), comment='最新回测ID')
    
    # 元数据
    added_at = Column(DateTime, default=datetime.now, comment='添加时间')
    notes = Column(Text, comment='备注')
    
    def __repr__(self):
        return f"<FavoriteStock(id={self.id}, symbol={self.symbol}, name={self.name})>"
