"""
Strategy and signal-related Pydantic models for API.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class SignalType(str, Enum):
    """Trading signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class StrategyType(str, Enum):
    """Available strategy types."""
    MA_CROSSOVER = "ma_crossover"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER = "bollinger"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    ALL = "all"


class StrategyAnalysisRequest(BaseModel):
    """Request model for strategy analysis."""
    symbol: str = Field(..., description="Stock symbol to analyze")
    strategies: List[StrategyType] = Field(default=[StrategyType.ALL], description="Strategies to run")
    period: str = Field(default="1mo", description="Data period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max")
    interval: str = Field(default="1d", description="Data interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "strategies": ["ma_crossover", "rsi"],
                "period": "1mo",
                "interval": "1d"
            }
        }


class BatchAnalysisRequest(BaseModel):
    """Request model for batch strategy analysis."""
    symbols: List[str] = Field(..., description="List of symbols to analyze", min_items=1, max_items=50)
    strategies: List[StrategyType] = Field(default=[StrategyType.ALL])
    period: str = Field(default="1mo")
    interval: str = Field(default="1d")


class SignalResponse(BaseModel):
    """Response model for trading signal."""
    symbol: str
    signal_type: SignalType
    strategy: str
    confidence: float = Field(..., ge=0.0, le=1.0, description="Signal confidence score")
    price: float = Field(..., description="Current price")
    timestamp: str
    indicators: Dict[str, Any] = Field(default_factory=dict, description="Relevant indicator values")
    reason: Optional[str] = Field(None, description="Signal generation reason")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "signal_type": "buy",
                "strategy": "ma_crossover",
                "confidence": 0.85,
                "price": 175.23,
                "timestamp": "2025-10-22T10:00:00",
                "indicators": {
                    "ma_short": 174.50,
                    "ma_long": 172.30
                },
                "reason": "Short MA crossed above long MA"
            }
        }


class StrategyAnalysisResponse(BaseModel):
    """Response model for strategy analysis results."""
    symbol: str
    strategy: str
    signal: Optional[SignalResponse] = None
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    chart_data: Optional[Dict[str, Any]] = None
    analysis_time: str
    success: bool = True
    error: Optional[str] = None


class BatchAnalysisResponse(BaseModel):
    """Response model for batch analysis."""
    results: List[StrategyAnalysisResponse]
    total_analyzed: int
    successful: int
    failed: int
    execution_time: float = Field(..., description="Total execution time in seconds")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Aggregated summary statistics")
