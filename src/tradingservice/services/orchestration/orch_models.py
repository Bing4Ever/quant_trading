#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestration service models.

This module encapsulates dataclasses and enums that represent task-level
concepts used across the orchestration layer, keeping ``task_manager`` focused
on coordination logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(Enum):
    """Lifecycle states for orchestration tasks."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class Task:
    """Internal representation of an orchestration task."""

    task_id: str
    name: str
    symbols: List[str]
    strategies: List[str]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the task into a plain dictionary."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "symbols": self.symbols,
            "strategies": self.strategies,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "result": self.result,
            "error": self.error,
        }


__all__ = ["TaskStatus", "Task"]
