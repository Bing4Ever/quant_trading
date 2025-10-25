"""
Portfolio and risk management models for API.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class PositionModel(BaseModel):
    """Individual position in portfolio."""
    symbol: str
    quantity: float = Field(..., gt=0)
    entry_price: float = Field(..., gt=0)
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    weight: Optional[float] = Field(None, ge=0, le=1, description="Position weight in portfolio")


class PortfolioSummary(BaseModel):
    """Portfolio summary statistics."""
    total_value: float
    cash: float
    invested_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    position_count: int
    positions: List[PositionModel]
    last_updated: str


class TradeRequest(BaseModel):
    """Request model for executing a trade."""
    symbol: str = Field(..., description="Stock symbol")
    action: str = Field(..., description="Trade action: buy or sell")
    quantity: float = Field(..., gt=0)
    order_type: str = Field(default="market", description="Order type: market, limit, stop")
    limit_price: Optional[float] = Field(None, gt=0, description="Limit price for limit orders")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "action": "buy",
                "quantity": 10,
                "order_type": "market"
            }
        }


class TradeResponse(BaseModel):
    """Response model for trade execution."""
    trade_id: str
    symbol: str
    action: str
    quantity: float
    executed_price: float
    total_cost: float
    commission: float
    status: str = Field(..., description="Trade status: filled, partial, pending, rejected")
    timestamp: str
    message: Optional[str] = None


class RiskMetrics(BaseModel):
    """Portfolio risk metrics."""
    portfolio_var: float = Field(..., description="Value at Risk")
    portfolio_cvar: float = Field(..., description="Conditional Value at Risk")
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    volatility: Optional[float] = None
    beta: Optional[float] = None


class PortfolioOptimizationRequest(BaseModel):
    """Request for portfolio optimization."""
    symbols: List[str] = Field(..., min_items=2, max_items=100)
    target_return: Optional[float] = Field(None, description="Target annual return")
    risk_tolerance: str = Field(default="moderate", description="Risk tolerance: conservative, moderate, aggressive")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Optimization constraints")


class PortfolioOptimizationResponse(BaseModel):
    """Response with optimized portfolio allocation."""
    allocations: Dict[str, float] = Field(..., description="Symbol to weight mapping")
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    risk_metrics: RiskMetrics
    optimization_method: str
