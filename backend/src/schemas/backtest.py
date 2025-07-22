"""Backtest-related schemas for API endpoints."""

from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from ..models.backtest import BacktestStatus, BacktestProvider


class BacktestBase(BaseModel):
    """Base backtest schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: date
    end_date: date
    initial_capital: float = Field(..., gt=0)
    provider: BacktestProvider


class BacktestCreate(BacktestBase):
    """Schema for creating a backtest."""
    
    strategy_id: int
    configuration: Dict = Field(default_factory=dict)


class BacktestUpdate(BaseModel):
    """Schema for updating a backtest."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[BacktestStatus] = None


class BacktestResponse(BaseModel):
    """Backtest response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    
    # Configuration
    start_date: date
    end_date: date
    initial_capital: float
    provider: BacktestProvider
    configuration: Dict
    
    # Status
    status: BacktestStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    
    # Results
    total_return: Optional[float]
    annualized_return: Optional[float]
    volatility: Optional[float]
    sharpe_ratio: Optional[float]
    sortino_ratio: Optional[float]
    max_drawdown: Optional[float]
    win_rate: Optional[float]
    
    # Detailed results
    equity_curve: Optional[Dict]
    trades: Optional[Dict]
    statistics: Optional[Dict]
    
    # Relations
    strategy_id: int
    created_by_id: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime


class BacktestListResponse(BaseModel):
    """Response for backtest list endpoints."""
    
    backtests: List[BacktestResponse]
    total: int
    skip: int
    limit: int


class BacktestResultsUpload(BaseModel):
    """Schema for uploading backtest results."""
    
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: Optional[float] = None
    max_drawdown: float
    win_rate: float
    equity_curve: Optional[Dict] = None
    trades: Optional[Dict] = None
    statistics: Optional[Dict] = None