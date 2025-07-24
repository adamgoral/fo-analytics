"""Portfolio optimization and analysis schemas."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime


class PortfolioOptimizationRequest(BaseModel):
    """Request schema for portfolio optimization."""
    symbols: List[str] = Field(..., description="List of asset symbols")
    start_date: datetime = Field(..., description="Start date for historical data")
    end_date: datetime = Field(..., description="End date for historical data")
    method: str = Field(..., description="Optimization method: mean_variance, max_sharpe, min_volatility, risk_parity, black_litterman")
    risk_free_rate: float = Field(0.02, description="Annual risk-free rate")
    
    # Mean-variance specific
    target_return: Optional[float] = Field(None, description="Target annual return for mean-variance optimization")
    constraints: Optional[List[Dict[str, Any]]] = Field(None, description="Additional optimization constraints")
    
    # Black-Litterman specific
    market_caps: Optional[Dict[str, float]] = Field(None, description="Market capitalizations for Black-Litterman")
    views: Optional[Dict[str, float]] = Field(None, description="Return views for specific assets")
    view_confidence: Optional[Dict[str, float]] = Field(None, description="Confidence in each view (0-1)")
    tau: Optional[float] = Field(0.05, description="Black-Litterman tau parameter")
    
    class Config:
        schema_extra = {
            "example": {
                "symbols": ["AAPL", "GOOGL", "MSFT", "AMZN"],
                "start_date": "2023-01-01T00:00:00",
                "end_date": "2024-01-01T00:00:00",
                "method": "max_sharpe",
                "risk_free_rate": 0.02
            }
        }


class PortfolioOptimizationResponse(BaseModel):
    """Response schema for portfolio optimization."""
    weights: Dict[str, float] = Field(..., description="Optimal portfolio weights")
    annual_return: float = Field(..., description="Expected annual return")
    annual_volatility: float = Field(..., description="Expected annual volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    success: bool = Field(..., description="Whether optimization succeeded")
    additional_metrics: Optional[Dict[str, Any]] = Field(None, description="Additional method-specific metrics")


class MultiStrategyBacktestRequest(BaseModel):
    """Request schema for multi-strategy backtest."""
    name: Optional[str] = Field(None, description="Backtest name")
    description: Optional[str] = Field(None, description="Backtest description")
    strategies: List[Dict[str, Any]] = Field(..., description="List of strategy configurations")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(10000.0, description="Starting capital")
    symbols: Optional[List[str]] = Field(None, description="Symbols to trade")
    optimization_method: str = Field("equal_weight", description="Portfolio optimization method")
    optimization_params: Optional[Dict[str, Any]] = Field(None, description="Optimization parameters")
    rebalance_frequency: str = Field("monthly", description="Rebalance frequency: daily, weekly, monthly, quarterly, yearly")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Multi-Strategy Portfolio Test",
                "strategies": [
                    {
                        "type": "sma_crossover",
                        "parameters": {"fast_period": 10, "slow_period": 20},
                        "risk_parameters": {"position_size": 0.95}
                    },
                    {
                        "type": "rsi_mean_reversion",
                        "parameters": {"rsi_period": 14, "oversold_level": 30, "overbought_level": 70},
                        "risk_parameters": {"position_size": 0.95}
                    }
                ],
                "start_date": "2023-01-01T00:00:00",
                "end_date": "2024-01-01T00:00:00",
                "initial_capital": 10000,
                "optimization_method": "risk_parity",
                "rebalance_frequency": "monthly"
            }
        }


class MultiStrategyBacktestResponse(BaseModel):
    """Response schema for multi-strategy backtest."""
    backtest_id: int = Field(..., description="Backtest ID")
    results: Dict[str, Any] = Field(..., description="Backtest results")
    status: str = Field(..., description="Backtest status")


class EfficientFrontierRequest(BaseModel):
    """Request schema for efficient frontier calculation."""
    symbols: List[str] = Field(..., description="List of asset symbols")
    start_date: datetime = Field(..., description="Start date for historical data")
    end_date: datetime = Field(..., description="End date for historical data")
    risk_free_rate: float = Field(0.02, description="Annual risk-free rate")
    n_portfolios: int = Field(50, description="Number of portfolios on frontier")


class EfficientFrontierResponse(BaseModel):
    """Response schema for efficient frontier."""
    portfolios: List[Dict[str, Any]] = Field(..., description="List of efficient portfolios")
    symbols: List[str] = Field(..., description="Asset symbols")


class RiskMetricsRequest(BaseModel):
    """Request schema for risk metrics calculation."""
    returns: List[float] = Field(..., description="List of returns (daily)")
    benchmark_returns: Optional[List[float]] = Field(None, description="Benchmark returns for relative metrics")
    confidence_levels: Optional[List[float]] = Field([0.95, 0.99], description="Confidence levels for VaR/CVaR")
    
    class Config:
        schema_extra = {
            "example": {
                "returns": [0.01, -0.02, 0.015, 0.005, -0.01, 0.02],
                "confidence_levels": [0.95, 0.99]
            }
        }


class RiskMetricsResponse(BaseModel):
    """Response schema for risk metrics."""
    metrics: Dict[str, Any] = Field(..., description="Calculated risk metrics")