"""
API Dependencies

Dependency injection providers for FastAPI.
"""

from functools import lru_cache
from src.tradingservice.services.automation import (
    AutoTradingScheduler as AutomationScheduler,
)


# Global scheduler instance
_scheduler_instance = None


def get_scheduler() -> AutomationScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = AutomationScheduler()
    return _scheduler_instance


@lru_cache()
def get_config():
    """Get application configuration."""
    from api.config import settings

    return settings
