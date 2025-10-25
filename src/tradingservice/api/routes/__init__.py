"""
API Routes Package

FastAPI route handlers organized by domain.
"""

from api.routes import tasks
from api.routes import scheduler
from api.routes import strategies

__all__ = [
    "tasks",
    "scheduler",
    "strategies",
]
