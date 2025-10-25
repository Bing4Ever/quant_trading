"""
Quantitative Trading System - FastAPI Application

Main application entry point for the REST API backend.
Provides comprehensive endpoints for task management, strategy analysis,
portfolio management, and real-time data streaming.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .middleware import (
    LoggingMiddleware,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from .routes import tasks, scheduler, strategies
from .dependencies import get_scheduler
from .models.common_models import HealthCheckResponse


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/api.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    # Startup
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 60)
    
    # Initialize scheduler
    try:
        scheduler_instance = get_scheduler()
        logger.info(f"✓ Scheduler initialized: {type(scheduler_instance).__name__}")
    except Exception as e:
        logger.error(f"✗ Failed to initialize scheduler: {e}")
    
    # Create necessary directories
    Path(settings.CONFIG_DIR).mkdir(exist_ok=True)
    Path(settings.LOGS_DIR).mkdir(exist_ok=True)
    logger.info("✓ Data directories verified")
    
    logger.info(f"✓ Server ready on {settings.HOST}:{settings.PORT}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    try:
        scheduler_instance = get_scheduler()
        if scheduler_instance.is_running:
            scheduler_instance.stop()
            logger.info("✓ Scheduler stopped")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    **Quantitative Trading System REST API**
    
    A comprehensive backend API for automated trading operations:
    
    * **Task Management**: Create, update, delete, and execute automated trading tasks
    * **Strategy Analysis**: Run technical analysis strategies and generate signals
    * **Scheduler Control**: Manage the task scheduler lifecycle
    * **Real-time Data**: WebSocket endpoints for live market data and signals
    
    ## Authentication
    Authentication is optional and can be enabled via environment configuration.
    
    ## Rate Limiting
    Rate limiting can be configured per environment.
    
    ## Support
    For issues and support, please refer to the project documentation.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)


# Add custom middleware
app.add_middleware(LoggingMiddleware)


# Register exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# Include routers
app.include_router(tasks.router)
app.include_router(scheduler.router)
app.include_router(strategies.router)


# Health check endpoint
@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["System"],
    summary="Health check",
    description="Check the health status of the API and its dependencies."
)
async def health_check() -> HealthCheckResponse:
    """Check API health status."""
    try:
        scheduler_instance = get_scheduler()
        scheduler_status = "healthy" if scheduler_instance else "unhealthy"
    except Exception:
        scheduler_status = "unhealthy"
    
    # Determine overall status
    if scheduler_status == "healthy":
        status = "healthy"
    else:
        status = "degraded"
    
    return HealthCheckResponse(
        status=status,
        version=settings.APP_VERSION,
        uptime_seconds=0.0,  # TODO: Track actual uptime
        dependencies={
            "scheduler": scheduler_status,
        },
        timestamp=datetime.now().isoformat()
    )


# Root endpoint
@app.get(
    "/",
    tags=["System"],
    summary="API root",
    description="Get basic API information and available endpoints."
)
async def root():
    """API root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs_url": "/docs",
        "health_check": "/health",
        "endpoints": {
            "tasks": "/api/tasks",
            "scheduler": "/api/scheduler",
            "strategies": "/api/strategies"
        }
    }


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.tradingservice.api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS,
        log_level="info"
    )
