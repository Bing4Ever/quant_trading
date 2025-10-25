"""
Scheduler Control Routes

API endpoints for managing the task scheduler.
"""

from fastapi import APIRouter, HTTPException, Depends, status

from api.models.scheduler_models import SchedulerStatus, SchedulerControlResponse
from api.models.common_models import ErrorResponse
from api.services.scheduler_service import SchedulerService


router = APIRouter(prefix="/api/scheduler", tags=["Scheduler"])


def get_scheduler_service() -> SchedulerService:
    """Dependency injection for scheduler service."""
    from api.dependencies import get_scheduler
    scheduler = get_scheduler()
    return SchedulerService(scheduler)


@router.get(
    "/status",
    response_model=SchedulerStatus,
    summary="Get scheduler status",
    description="Retrieve current status of the task scheduler including uptime and task counts."
)
async def get_status(
    service: SchedulerService = Depends(get_scheduler_service)
) -> SchedulerStatus:
    """Get current scheduler status."""
    return service.get_status()


@router.post(
    "/start",
    response_model=SchedulerControlResponse,
    summary="Start the scheduler",
    description="Start the task scheduler to begin automated task execution.",
    responses={500: {"model": ErrorResponse, "description": "Failed to start scheduler"}}
)
async def start_scheduler(
    service: SchedulerService = Depends(get_scheduler_service)
) -> SchedulerControlResponse:
    """Start the scheduler."""
    try:
        return service.start_scheduler()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start scheduler: {str(e)}"
        )


@router.post(
    "/stop",
    response_model=SchedulerControlResponse,
    summary="Stop the scheduler",
    description="Stop the task scheduler and halt all automated task execution.",
    responses={500: {"model": ErrorResponse, "description": "Failed to stop scheduler"}}
)
async def stop_scheduler(
    service: SchedulerService = Depends(get_scheduler_service)
) -> SchedulerControlResponse:
    """Stop the scheduler."""
    try:
        return service.stop_scheduler()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop scheduler: {str(e)}"
        )


@router.post(
    "/restart",
    response_model=SchedulerControlResponse,
    summary="Restart the scheduler",
    description="Restart the task scheduler (stop then start).",
    responses={500: {"model": ErrorResponse, "description": "Failed to restart scheduler"}}
)
async def restart_scheduler(
    service: SchedulerService = Depends(get_scheduler_service)
) -> SchedulerControlResponse:
    """Restart the scheduler."""
    try:
        return service.restart_scheduler()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart scheduler: {str(e)}"
        )
