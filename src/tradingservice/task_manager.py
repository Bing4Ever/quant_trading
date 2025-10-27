#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task manager facade.

This module keeps backwards compatibility by re-exporting the concrete
implementation that lives under ``services.orchestration.task_manager``.
"""

from src.tradingservice.services.orchestration import (  # noqa: F401
    TaskManager,
    Task,
    TaskStatus,
)

__all__ = ["TaskManager", "Task", "TaskStatus"]
