"""Message schemas for backtest processing."""

from datetime import date
from pydantic import BaseModel, Field
from typing import Dict, Any

from models.backtest import BacktestProvider


class BacktestMessage(BaseModel):
    """Message schema for backtest processing."""
    
    backtest_id: int = Field(..., description="ID of the backtest to process")
    strategy_id: int = Field(..., description="ID of the strategy to backtest")
    start_date: date = Field(..., description="Start date for backtesting")
    end_date: date = Field(..., description="End date for backtesting")
    initial_capital: float = Field(..., gt=0, description="Initial capital for backtesting")
    provider: BacktestProvider = Field(..., description="Backtesting provider to use")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }