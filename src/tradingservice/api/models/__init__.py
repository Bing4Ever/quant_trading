"""
API Models Package

Pydantic models for request/response validation.
"""

from api.models.task_models import (
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskResponse,
    TaskExecutionRequest,
    TaskExecutionResponse,
    TaskListResponse,
    ScheduleFrequencyEnum
)

from api.models.strategy_models import (
    StrategyAnalysisRequest,
    BatchAnalysisRequest,
    SignalResponse,
    StrategyAnalysisResponse,
    BatchAnalysisResponse,
    SignalType,
    StrategyType
)

from api.models.portfolio_models import (
    PositionModel,
    PortfolioSummary,
    TradeRequest,
    TradeResponse,
    RiskMetrics,
    PortfolioOptimizationRequest,
    PortfolioOptimizationResponse
)

from api.models.scheduler_models import (
    SchedulerStatus,
    SchedulerControlResponse,
    SchedulerExecutionHistoryResponse,
    SchedulerExecutionRecord,
    SchedulerExecutionOrder,
    SchedulerRiskSnapshot,
)

from api.models.common_models import (
    SuccessResponse,
    ErrorResponse,
    HealthCheckResponse
)

__all__ = [
    # Task models
    "TaskCreateRequest",
    "TaskUpdateRequest",
    "TaskResponse",
    "TaskExecutionRequest",
    "TaskExecutionResponse",
    "TaskListResponse",
    "ScheduleFrequencyEnum",
    
    # Strategy models
    "StrategyAnalysisRequest",
    "BatchAnalysisRequest",
    "SignalResponse",
    "StrategyAnalysisResponse",
    "BatchAnalysisResponse",
    "SignalType",
    "StrategyType",
    
    # Portfolio models
    "PositionModel",
    "PortfolioSummary",
    "TradeRequest",
    "TradeResponse",
    "RiskMetrics",
    "PortfolioOptimizationRequest",
    "PortfolioOptimizationResponse",
    
    # Scheduler models
    "SchedulerStatus",
    "SchedulerControlResponse",
    "SchedulerExecutionHistoryResponse",
    "SchedulerExecutionRecord",
    "SchedulerExecutionOrder",
    "SchedulerRiskSnapshot",
    
    # Common models
    "SuccessResponse",
    "ErrorResponse",
    "HealthCheckResponse",
]
