"""
Optimization Record Model - 参数优化记录模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from src.common.dataaccess import OrmBase


class OptimizationRecord(OrmBase):
    """参数优化记录模型"""

    __tablename__ = "optimization_history"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 优化信息
    symbol = Column(String(20), nullable=False, index=True, comment="股票代码")
    parameter_name = Column(String(100), nullable=False, comment="参数名称")
    parameter_value = Column(Text, nullable=False, comment="参数值")
    performance_metric = Column(Float, comment="性能指标值")
    metric_type = Column(String(50), nullable=False, comment="指标类型")

    # 元数据
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    def __repr__(self):
        return f"<OptimizationRecord(id={self.id}, symbol={self.symbol}, param={self.parameter_name})>"
