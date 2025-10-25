"""
Scheduler-related models for API.
"""

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
