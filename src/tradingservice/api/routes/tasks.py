"""
Task Management Routes

API endpoints for creating, reading, updating, and deleting automated trading tasks.
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status

from api.models.task_models import (
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskResponse,
    TaskExecutionRequest,
    TaskExecutionResponse,
    TaskListResponse
)
from api.models.common_models import SuccessResponse, ErrorResponse
from api.services.task_service import TaskService


router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


def get_task_service() -> TaskService:
    """Dependency injection for task service."""
    from api.dependencies import get_scheduler
    scheduler = get_scheduler()
    return TaskService(scheduler)


@router.get(
    "",
    response_model=TaskListResponse,
    summary="Get all tasks",
    description="Retrieve a list of all automated trading tasks with summary statistics."
)
async def get_tasks(service: TaskService = Depends(get_task_service)) -> TaskListResponse:
    """Get all tasks."""
    return service.get_all_tasks()


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task by ID",
    description="Retrieve detailed information about a specific task.",
    responses={404: {"model": ErrorResponse, "description": "Task not found"}}
)
async def get_task(
    task_id: str,
    service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """Get a specific task by ID."""
    task = service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    return task


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="Create a new automated trading task with specified parameters.",
    responses={400: {"model": ErrorResponse, "description": "Invalid request data"}}
)
async def create_task(
    request: TaskCreateRequest,
    service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """Create a new scheduled task."""
    try:
        return service.create_task(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
    description="Update an existing task's configuration.",
    responses={404: {"model": ErrorResponse, "description": "Task not found"}}
)
async def update_task(
    task_id: str,
    request: TaskUpdateRequest,
    service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """Update an existing task."""
    try:
        task = service.update_task(task_id, request)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        return task
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )


@router.delete(
    "/{task_id}",
    response_model=SuccessResponse,
    summary="Delete a task",
    description="Permanently delete a task.",
    responses={404: {"model": ErrorResponse, "description": "Task not found"}}
)
async def delete_task(
    task_id: str,
    service: TaskService = Depends(get_task_service)
) -> SuccessResponse:
    """Delete a task."""
    try:
        result = service.delete_task(task_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        return SuccessResponse(
            success=True,
            message=f"Task {task_id} deleted successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )


@router.post(
    "/{task_id}/execute",
    response_model=TaskExecutionResponse,
    summary="Execute a task manually",
    description="Trigger immediate execution of a task, optionally in async mode.",
    responses={404: {"model": ErrorResponse, "description": "Task not found"}}
)
async def execute_task(
    task_id: str,
    request: TaskExecutionRequest = TaskExecutionRequest(),
    service: TaskService = Depends(get_task_service)
) -> TaskExecutionResponse:
    """Execute a task manually."""
    result = service.execute_task(task_id, request.async_mode)
    if result.status == "failed" and "not found" in result.message.lower():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.message
        )
    return result


@router.post(
    "/{task_id}/pause",
    response_model=SuccessResponse,
    summary="Pause a task",
    description="Temporarily pause task execution.",
    responses={404: {"model": ErrorResponse, "description": "Task not found"}}
)
async def pause_task(
    task_id: str,
    service: TaskService = Depends(get_task_service)
) -> SuccessResponse:
    """Pause a task."""
    try:
        result = service.pause_task(task_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        return SuccessResponse(
            success=True,
            message=f"Task {task_id} paused successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause task: {str(e)}"
        )


@router.post(
    "/{task_id}/resume",
    response_model=SuccessResponse,
    summary="Resume a task",
    description="Resume a paused task.",
    responses={404: {"model": ErrorResponse, "description": "Task not found"}}
)
async def resume_task(
    task_id: str,
    service: TaskService = Depends(get_task_service)
) -> SuccessResponse:
    """Resume a paused task."""
    try:
        result = service.resume_task(task_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        return SuccessResponse(
            success=True,
            message=f"Task {task_id} resumed successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume task: {str(e)}"
        )
