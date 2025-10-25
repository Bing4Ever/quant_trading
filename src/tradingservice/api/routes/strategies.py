"""
Strategy Analysis Routes

API endpoints for running strategy analysis and generating trading signals.
"""

from fastapi import APIRouter, HTTPException, Depends, status

from api.models.strategy_models import (
    StrategyAnalysisRequest,
    BatchAnalysisRequest,
    StrategyAnalysisResponse,
    BatchAnalysisResponse
)
from api.models.common_models import ErrorResponse
from api.services.strategy_service import StrategyService


router = APIRouter(prefix="/api/strategies", tags=["Strategies"])


def get_strategy_service() -> StrategyService:
    """Dependency injection for strategy service."""
    return StrategyService()


@router.post(
    "/analyze",
    response_model=StrategyAnalysisResponse,
    summary="Analyze a symbol",
    description="Run strategy analysis on a single symbol to generate trading signals.",
    responses={400: {"model": ErrorResponse, "description": "Invalid request"}}
)
async def analyze_symbol(
    request: StrategyAnalysisRequest,
    service: StrategyService = Depends(get_strategy_service)
) -> StrategyAnalysisResponse:
    """Analyze a single symbol with specified strategies."""
    try:
        return service.analyze_symbol(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post(
    "/batch-analyze",
    response_model=BatchAnalysisResponse,
    summary="Batch analyze multiple symbols",
    description="Run strategy analysis on multiple symbols in parallel for efficient processing.",
    responses={400: {"model": ErrorResponse, "description": "Invalid request"}}
)
async def batch_analyze(
    request: BatchAnalysisRequest,
    service: StrategyService = Depends(get_strategy_service)
) -> BatchAnalysisResponse:
    """Analyze multiple symbols in parallel."""
    try:
        return service.batch_analyze(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}"
        )


@router.get(
    "/available",
    summary="Get available strategies",
    description="List all available trading strategies that can be used for analysis."
)
async def get_available_strategies():
    """Get list of available strategies."""
    return {
        "strategies": [
            {
                "name": "ma_crossover",
                "description": "Moving Average Crossover Strategy",
                "parameters": ["short_window", "long_window"]
            },
            {
                "name": "rsi",
                "description": "Relative Strength Index Strategy",
                "parameters": ["period", "overbought", "oversold"]
            },
            {
                "name": "macd",
                "description": "MACD Strategy",
                "parameters": ["fast", "slow", "signal"]
            },
            {
                "name": "bollinger",
                "description": "Bollinger Bands Strategy",
                "parameters": ["period", "std_dev"]
            },
            {
                "name": "mean_reversion",
                "description": "Mean Reversion Strategy",
                "parameters": ["lookback_period", "std_threshold"]
            },
            {
                "name": "momentum",
                "description": "Momentum Strategy",
                "parameters": ["period"]
            }
        ]
    }
