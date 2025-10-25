"""
Common response models used across the API.
"""

from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Generic error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status: healthy, degraded, unhealthy")
    version: str
    uptime_seconds: float
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Status of dependencies")
    timestamp: str
