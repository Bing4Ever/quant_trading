"""
Scheduler Service Layer

Business logic for scheduler management operations.
"""

import time
import logging
from typing import Optional
from datetime import datetime

from automation.scheduler import TaskScheduler
from api.models.scheduler_models import SchedulerStatus, SchedulerControlResponse


logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing the task scheduler."""
    
    def __init__(self, scheduler: TaskScheduler):
        """Initialize scheduler service."""
        self.scheduler = scheduler
        self.start_time = time.time()
    
    def get_status(self) -> SchedulerStatus:
        """Get current scheduler status."""
        tasks = self.scheduler.get_all_tasks()
        running_tasks = sum(1 for t in tasks if t.get('enabled', False))
        
        return SchedulerStatus(
            is_running=self.scheduler.is_running,
            task_count=len(tasks),
            running_tasks=running_tasks,
            uptime_seconds=time.time() - self.start_time if self.scheduler.is_running else 0,
            last_execution=None,  # TODO: Track last execution
            next_execution=None   # TODO: Calculate next execution
        )
    
    def start_scheduler(self) -> SchedulerControlResponse:
        """Start the scheduler."""
        if self.scheduler.is_running:
            return SchedulerControlResponse(
                status="already_running",
                message="Scheduler is already running",
                current_status=self.get_status()
            )
        
        try:
            self.scheduler.start()
            self.start_time = time.time()
            logger.info("Scheduler started successfully")
            
            return SchedulerControlResponse(
                status="started",
                message="Scheduler started successfully",
                current_status=self.get_status()
            )
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise
    
    def stop_scheduler(self) -> SchedulerControlResponse:
        """Stop the scheduler."""
        if not self.scheduler.is_running:
            return SchedulerControlResponse(
                status="already_stopped",
                message="Scheduler is already stopped",
                current_status=self.get_status()
            )
        
        try:
            self.scheduler.stop()
            logger.info("Scheduler stopped successfully")
            
            return SchedulerControlResponse(
                status="stopped",
                message="Scheduler stopped successfully",
                current_status=self.get_status()
            )
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}")
            raise
    
    def restart_scheduler(self) -> SchedulerControlResponse:
        """Restart the scheduler."""
        try:
            if self.scheduler.is_running:
                self.scheduler.stop()
            
            time.sleep(0.5)  # Brief pause
            
            self.scheduler.start()
            self.start_time = time.time()
            logger.info("Scheduler restarted successfully")
            
            return SchedulerControlResponse(
                status="restarted",
                message="Scheduler restarted successfully",
                current_status=self.get_status()
            )
        except Exception as e:
            logger.error(f"Failed to restart scheduler: {e}")
            raise
