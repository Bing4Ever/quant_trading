"""
策略参数优化记录 ORM 模型。

用于追踪策略参数调优的历史结果。
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from src.common.dataaccess import OrmBase


class OptimizationRecord(OrmBase):
    """策略优化结果的历史记录实体。"""

    __tablename__ = "optimization_history"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 优化相关信息
    symbol = Column(String(20), nullable=False, index=True, comment="Ticker symbol")
    parameter_name = Column(
        String(100), nullable=False, comment="Name of the parameter being optimized"
    )
    parameter_value = Column(
        Text, nullable=False, comment="Serialized parameter value (JSON formatted)"
    )
    performance_metric = Column(
        Float, comment="Metric value produced by the optimization run"
    )
    metric_type = Column(
        String(50),
        nullable=False,
        comment="Type of performance metric (e.g. sharpe_ratio, total_return)",
    )

    # 审计信息
    created_at = Column(
        DateTime, default=datetime.now, comment="Record creation timestamp"
    )

    def __repr__(self) -> str:
        return (
            f"<OptimizationRecord(id={self.id}, symbol={self.symbol}, "
            f"param={self.parameter_name})>"
        )
