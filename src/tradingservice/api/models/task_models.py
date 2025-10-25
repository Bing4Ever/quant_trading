"""
Task-related Pydantic models for API request/response validation.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ScheduleFrequencyEnum(str, Enum):
    """Task execution frequency options."""
    MINUTE = "minute"
    EVERY_5_MINUTES = "5min"
    EVERY_15_MINUTES = "15min"
    EVERY_30_MINUTES = "30min"
    HOUR = "hour"
    EVERY_2_HOURS = "2hour"
    EVERY_4_HOURS = "4hour"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class TaskCreateRequest(BaseModel):
    """Request model for creating a new task."""
    name: str = Field(..., description="Task name", min_length=1, max_length=100)
    frequency: ScheduleFrequencyEnum = Field(..., description="Execution frequency")
    symbols: List[str] = Field(..., description="List of stock symbols to analyze", min_items=1, max_items=50)
    strategies: List[str] = Field(default=["all"], description="Strategy types to execute")
    enabled: bool = Field(default=True, description="Whether the task is enabled")
    description: Optional[str] = Field(None, description="Task description", max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Daily AAPL Analysis",
                "frequency": "daily",
                "symbols": ["AAPL", "MSFT"],
                "strategies": ["all"],
                "enabled": True,
                "description": "Analyze tech stocks daily"
            }
        }


class TaskUpdateRequest(BaseModel):
    """Request model for updating a task."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    frequency: Optional[ScheduleFrequencyEnum] = None
    symbols: Optional[List[str]] = Field(None, min_items=1, max_items=50)
    strategies: Optional[List[str]] = None
    enabled: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=500)


class TaskResponse(BaseModel):
    """Response model for task information."""
    task_id: str = Field(..., description="Unique task identifier")
    name: str
    frequency: str
    symbols: List[str]
    strategies: List[str]
    enabled: bool
    created_at: str
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = Field(default=0, description="Number of times task has been executed")
    description: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_1729567890",
                "name": "Daily AAPL Analysis",
                "frequency": "daily",
                "symbols": ["AAPL", "MSFT"],
                "strategies": ["all"],
                "enabled": True,
                "created_at": "2025-10-22T10:00:00",
                "last_run": "2025-10-22T10:05:00",
                "next_run": "2025-10-23T10:00:00",
                "run_count": 5,
                "description": "Analyze tech stocks daily"
            }
        }


class TaskExecutionRequest(BaseModel):
    """Request model for manual task execution."""
    async_mode: bool = Field(default=False, description="Execute task asynchronously")


class TaskExecutionResponse(BaseModel):
    """Response model for task execution."""
    task_id: str
    status: str = Field(..., description="Execution status: success, failed, running")
    message: str
    execution_time: Optional[float] = Field(None, description="Execution duration in seconds")
    results: Optional[Dict[str, Any]] = Field(None, description="Execution results")
    error: Optional[str] = None


class TaskListResponse(BaseModel):
    """Response model for task list."""
    tasks: List[TaskResponse]
    total: int
    enabled_count: int
    disabled_count: int
