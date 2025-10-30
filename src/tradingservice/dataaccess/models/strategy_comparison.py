"""
策略对比 ORM 模型。

用于保存多策略对比时的聚合结果。
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from src.common.dataaccess import OrmBase


class StrategyComparison(OrmBase):
    """策略对比结果的汇总实体。"""

    __tablename__ = "strategy_comparison"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 对比元数据
    comparison_name = Column(
        String(200), nullable=False, comment="Comparison task name"
    )
    symbols = Column(
        Text,
        nullable=False,
        comment="Symbols included in the comparison (JSON formatted)",
    )
    results = Column(
        Text,
        nullable=False,
        comment="Serialized comparison results (JSON formatted)",
    )
    best_performer = Column(
        String(100), comment="Best performing strategy or instrument"
    )

    # 审计信息
    created_at = Column(
        DateTime, default=datetime.now, comment="Record creation timestamp"
    )

    def __repr__(self) -> str:
        return f"<StrategyComparison(id={self.id}, name={self.comparison_name})>"
