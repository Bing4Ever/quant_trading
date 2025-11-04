"""
调度执行持久化模型。

提供自动化任务执行记录、生成的订单及风险快照的 SQLAlchemy ORM 定义。
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from src.common.dataaccess import OrmBase


class AutomationTaskExecution(OrmBase):
    """自动化任务的一次执行记录。"""

    __tablename__ = "automation_task_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(
        String(36),
        default=lambda: str(uuid4()),
        unique=True,
        nullable=False,
        index=True,
        comment="执行批次的唯一标识（UUID）",
    )

    task_id = Column(String(128), nullable=False, index=True, comment="调度任务 ID")
    task_name = Column(String(255), nullable=False, comment="任务名称")
    scheduler_status = Column(String(32), nullable=False, comment="调度层状态")
    orchestration_status = Column(
        String(32),
        nullable=False,
        comment="TaskManager 返回的状态",
    )

    started_at = Column(DateTime, nullable=True, comment="执行开始时间")
    completed_at = Column(DateTime, nullable=True, comment="执行结束时间")

    executed_signals = Column(Integer, default=0, comment="通过风控的信号数量")
    rejected_signals = Column(Integer, default=0, comment="被拒绝的信号数量")
    total_signals = Column(Integer, default=0, comment="总信号数量")
    order_count = Column(Integer, default=0, comment="执行生成的订单数量")

    task_errors_json = Column(Text, comment="任务错误列表（JSON）")
    symbol_details_json = Column(Text, comment="标的维度的执行详情（JSON）")
    summary_json = Column(Text, comment="执行摘要（JSON）")
    account_snapshot_json = Column(Text, comment="账户快照（JSON）")
    payload_json = Column(Text, comment="TaskManager 原始执行结果（JSON）")

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="记录创建时间（UTC）",
    )

    orders = relationship(
        "AutomationTaskOrder",
        back_populates="execution",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    risk_snapshot = relationship(
        "AutomationRiskSnapshot",
        back_populates="execution",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<AutomationTaskExecution(run_id={self.run_id}, task_id={self.task_id})>"


class AutomationTaskOrder(OrmBase):
    """自动化任务执行过程中生成的订单记录。"""

    __tablename__ = "automation_task_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(
        Integer,
        ForeignKey("automation_task_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    order_id = Column(String(128), nullable=False, index=True, comment="券商返回的订单 ID")
    symbol = Column(String(32), nullable=True, comment="交易标的")
    action = Column(String(16), nullable=True, comment="方向（买/卖）")
    status = Column(String(32), nullable=True, comment="订单最新状态")
    quantity = Column(Float, nullable=True, comment="提交数量")
    filled_quantity = Column(Float, nullable=True, comment="成交数量")
    average_price = Column(Float, nullable=True, comment="成交均价")
    submitted_at = Column(DateTime, nullable=True, comment="提交时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    raw_order_json = Column(Text, comment="订单原始数据（JSON）")
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="记录创建时间（UTC）",
    )

    execution = relationship("AutomationTaskExecution", back_populates="orders")

    def __repr__(self) -> str:
        return f"<AutomationTaskOrder(order_id={self.order_id}, symbol={self.symbol})>"


class AutomationRiskSnapshot(OrmBase):
    """自动化任务执行后的风险指标快照。"""

    __tablename__ = "automation_risk_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(
        Integer,
        ForeignKey("automation_task_executions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    equity = Column(Float, nullable=True, comment="账户净值")
    cash = Column(Float, nullable=True, comment="可用现金")
    buying_power = Column(Float, nullable=True, comment="可用杠杆/购买力")
    exposure = Column(Float, nullable=True, comment="当前敞口")
    maintenance_margin = Column(Float, nullable=True, comment="维持保证金需求")

    raw_metrics_json = Column(Text, comment="风险指标原始数据（JSON）")
    captured_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="快照采集时间（UTC）",
    )

    execution = relationship("AutomationTaskExecution", back_populates="risk_snapshot")

    def __repr__(self) -> str:
        return f"<AutomationRiskSnapshot(execution_id={self.execution_id})>"
