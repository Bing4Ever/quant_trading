"""
Strategy Comparison Model - 策略对比模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from src.common.dataaccess import OrmBase


class StrategyComparison(OrmBase):
    """策略对比模型"""

    __tablename__ = "strategy_comparison"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 对比信息
    comparison_name = Column(String(200), nullable=False, comment="对比名称")
    symbols = Column(Text, nullable=False, comment="股票代码列表（JSON）")
    results = Column(Text, nullable=False, comment="对比结果（JSON）")
    best_performer = Column(String(100), comment="最佳表现者")

    # 元数据
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    def __repr__(self):
        return f"<StrategyComparison(id={self.id}, name={self.comparison_name})>"
