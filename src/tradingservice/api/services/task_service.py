"""
Task Service Layer

Business logic for task management operations.
Decouples API routes from core automation logic.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from automation.scheduler import TaskScheduler, ScheduleFrequency
from api.models.task_models import (
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskResponse,
    TaskExecutionResponse,
    TaskListResponse
)


logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing automated trading tasks."""
    
    def __init__(self, scheduler: TaskScheduler):
        """Initialize task service with scheduler instance."""
        self.scheduler = scheduler
    
    def get_all_tasks(self) -> TaskListResponse:
        """Get all tasks with summary statistics."""
        tasks_data = self.scheduler.get_all_tasks()
        task_responses = []
        
        for task_data in tasks_data:
            task_responses.append(TaskResponse(**task_data))
        
        enabled_count = sum(1 for t in task_responses if t.enabled)
        disabled_count = len(task_responses) - enabled_count
        
        return TaskListResponse(
            tasks=task_responses,
            total=len(task_responses),
            enabled_count=enabled_count,
            disabled_count=disabled_count
        )
    
    def get_task_by_id(self, task_id: str) -> Optional[TaskResponse]:
        """Get a specific task by ID."""
        task_data = self.scheduler.get_task_status(task_id)
        if not task_data:
            return None
        return TaskResponse(**task_data)
    
    def create_task(self, request: TaskCreateRequest) -> TaskResponse:
        """Create a new scheduled task."""
        try:
            # Convert string frequency to enum if needed
            if isinstance(request.frequency, str):
                frequency = ScheduleFrequency(request.frequency)
            else:
                frequency = request.frequency
            
            # Add task to scheduler
            task_id = self.scheduler.add_task(
                name=request.name,
                symbols=request.symbols,
                frequency=frequency,
                strategies=request.strategies,
                enabled=request.enabled
            )
            
            # Get created task details
            task_data = self.scheduler.get_task_status(task_id)
            if request.description:
                task_data['description'] = request.description
            
            logger.info(f"Created task: {task_id} - {request.name}")
            return TaskResponse(**task_data)
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise
    
    def update_task(self, task_id: str, request: TaskUpdateRequest) -> Optional[TaskResponse]:
        """Update an existing task."""
        # Verify task exists
        existing_task = self.scheduler.get_task_status(task_id)
        if not existing_task:
            return None
        
        try:
            # Update task properties
            update_data = request.model_dump(exclude_unset=True)
            
            # Handle frequency conversion
            if 'frequency' in update_data and update_data['frequency']:
                if isinstance(update_data['frequency'], str):
                    update_data['frequency'] = ScheduleFrequency(update_data['frequency'])
            
            # Apply updates (this is simplified - actual implementation would update scheduler)
            # For now, remove and re-add with updated data
            self.scheduler.remove_task(task_id)
            
            updated_data = {**existing_task, **update_data}
            new_task_id = self.scheduler.add_task(
                name=updated_data.get('name'),
                symbols=updated_data.get('symbols'),
                frequency=updated_data.get('frequency'),
                strategies=updated_data.get('strategies', ['all']),
                enabled=updated_data.get('enabled', True)
            )
            
            result = self.scheduler.get_task_status(new_task_id)
            logger.info(f"Updated task: {task_id} -> {new_task_id}")
            return TaskResponse(**result)
            
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            raise
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        try:
            result = self.scheduler.remove_task(task_id)
            if result:
                logger.info(f"Deleted task: {task_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            raise
    
    def execute_task(self, task_id: str, async_mode: bool = False) -> TaskExecutionResponse:
        """Execute a task manually."""
        task_data = self.scheduler.get_task_status(task_id)
        if not task_data:
            return TaskExecutionResponse(
                task_id=task_id,
                status="failed",
                message="Task not found",
                error="Task does not exist"
            )
        
        try:
            start_time = time.time()
            
            if async_mode:
                # TODO: Implement async execution with background tasks
                return TaskExecutionResponse(
                    task_id=task_id,
                    status="running",
                    message="Task execution started in background",
                    execution_time=0
                )
            else:
                # Synchronous execution
                self.scheduler.execute_task(task_id)
                execution_time = time.time() - start_time
                
                return TaskExecutionResponse(
                    task_id=task_id,
                    status="success",
                    message="Task executed successfully",
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Task execution failed for {task_id}: {e}")
            return TaskExecutionResponse(
                task_id=task_id,
                status="failed",
                message="Task execution failed",
                execution_time=execution_time,
                error=str(e)
            )
    
    def pause_task(self, task_id: str) -> bool:
        """Pause a task."""
        try:
            result = self.scheduler.pause_task(task_id)
            if result:
                logger.info(f"Paused task: {task_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to pause task {task_id}: {e}")
            raise
    
    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task."""
        try:
            result = self.scheduler.resume_task(task_id)
            if result:
                logger.info(f"Resumed task: {task_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to resume task {task_id}: {e}")
            raise
