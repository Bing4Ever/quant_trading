"""
Scheduler-related models for API.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SchedulerStatus(BaseModel):
    """Scheduler status information."""
    is_running: bool
    task_count: int
    running_tasks: int
    uptime_seconds: Optional[float] = None
    last_execution: Optional[str] = None
    next_execution: Optional[str] = None


class SchedulerControlResponse(BaseModel):
    """Response for scheduler control operations."""
    status: str = Field(..., description="Operation status: started, stopped, already_running, already_stopped")
    message: str
    current_status: SchedulerStatus


class SchedulerExecutionOrder(BaseModel):
    """Representation of an order attached to a scheduler execution run."""
    order_id: Optional[str]
    symbol: Optional[str]
    action: Optional[str]
    status: Optional[str]
    quantity: Optional[float]
    filled_quantity: Optional[float]
    average_price: Optional[float]
    submitted_at: Optional[datetime]
    completed_at: Optional[datetime]
    raw: Dict[str, Any]


class SchedulerRiskSnapshot(BaseModel):
    """Risk snapshot captured during scheduler execution."""
    equity: Optional[float]
    cash: Optional[float]
    buying_power: Optional[float]
    exposure: Optional[float]
    maintenance_margin: Optional[float]
    captured_at: Optional[datetime]
    raw: Dict[str, Any]


class SchedulerExecutionRecord(BaseModel):
    """Scheduler execution history record."""
    run_id: str
    task_id: str
    task_name: str
    scheduler_status: str
    orchestration_status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    executed_signals: Optional[int]
    rejected_signals: Optional[int]
    total_signals: Optional[int]
    order_count: Optional[int]
    task_errors: List[str]
    summary: Dict[str, Any]
    symbol_details: Dict[str, Any]
    account_snapshot: Dict[str, Any]
    payload: Dict[str, Any]
    orders: List[SchedulerExecutionOrder]
    risk_snapshot: Optional[SchedulerRiskSnapshot]
    created_at: Optional[datetime]


class SchedulerExecutionHistoryResponse(BaseModel):
    """Paginated-like wrapper for scheduler execution history."""
    count: int = Field(..., description="Number of records returned in this response")
    items: List[SchedulerExecutionRecord]
