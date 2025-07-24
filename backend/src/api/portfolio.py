"""Portfolio optimization API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog

from core.dependencies import get_current_user, get_db
from models.user import User, UserRole
from repositories.unit_of_work import UnitOfWork
from services.backtesting import (
    PortfolioOptimizer,
    MultiStrategyBacktester,
    RiskMetricsCalculator
)
from services.backtesting.data_loader import DataLoader
from schemas.portfolio import (
    PortfolioOptimizationRequest,
    PortfolioOptimizationResponse,
    MultiStrategyBacktestRequest,
    MultiStrategyBacktestResponse,
    EfficientFrontierRequest,
    EfficientFrontierResponse,
    RiskMetricsRequest,
    RiskMetricsResponse
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.post("/optimize", response_model=PortfolioOptimizationResponse)
async def optimize_portfolio(
    request: PortfolioOptimizationRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_db)
) -> PortfolioOptimizationResponse:
    """Optimize portfolio allocation using various methods."""
    try:
        # Load historical data
        data_loader = DataLoader()
        returns_data = await data_loader.load_returns_data(
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Create optimizer
        optimizer = PortfolioOptimizer(
            returns=returns_data,
            risk_free_rate=request.risk_free_rate
        )
        
        # Perform optimization based on method
        if request.method == "mean_variance":
            result = optimizer.mean_variance_optimization(
                target_return=request.target_return,
                constraints=request.constraints
            )
        elif request.method == "max_sharpe":
            result = optimizer.maximum_sharpe_portfolio()
        elif request.method == "min_volatility":
            result = optimizer.minimum_volatility_portfolio()
        elif request.method == "risk_parity":
            result = optimizer.risk_parity()
        elif request.method == "black_litterman":
            if not request.market_caps or not request.views:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Market caps and views required for Black-Litterman"
                )
            result = optimizer.black_litterman(
                market_caps=request.market_caps,
                views=request.views,
                view_confidence=request.view_confidence or {},
                tau=request.tau or 0.05
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown optimization method: {request.method}"
            )
        
        logger.info(
            "Portfolio optimization completed",
            user_id=current_user.id,
            method=request.method,
            symbols=request.symbols,
            success=result.get('success', True)
        )
        
        return PortfolioOptimizationResponse(
            weights=result['weights'],
            annual_return=result['annual_return'],
            annual_volatility=result['annual_volatility'],
            sharpe_ratio=result['sharpe_ratio'],
            success=result.get('success', True),
            additional_metrics=result.get('risk_contributions', {})
        )
        
    except Exception as e:
        logger.error(
            "Portfolio optimization failed",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Portfolio optimization failed: {str(e)}"
        )


@router.post("/efficient-frontier", response_model=EfficientFrontierResponse)
async def calculate_efficient_frontier(
    request: EfficientFrontierRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_db)
) -> EfficientFrontierResponse:
    """Calculate efficient frontier for given assets."""
    try:
        # Load historical data
        data_loader = DataLoader()
        returns_data = await data_loader.load_returns_data(
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Create optimizer
        optimizer = PortfolioOptimizer(
            returns=returns_data,
            risk_free_rate=request.risk_free_rate
        )
        
        # Generate efficient frontier
        frontier_df = optimizer.efficient_frontier(n_portfolios=request.n_portfolios)
        
        # Convert to response format
        portfolios = []
        for _, row in frontier_df.iterrows():
            portfolios.append({
                "weights": row['weights'],
                "annual_return": row['annual_return'],
                "annual_volatility": row['annual_volatility'],
                "sharpe_ratio": row['sharpe_ratio']
            })
        
        logger.info(
            "Efficient frontier calculated",
            user_id=current_user.id,
            symbols=request.symbols,
            portfolios=len(portfolios)
        )
        
        return EfficientFrontierResponse(
            portfolios=portfolios,
            symbols=request.symbols
        )
        
    except Exception as e:
        logger.error(
            "Efficient frontier calculation failed",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Efficient frontier calculation failed: {str(e)}"
        )


@router.post("/multi-strategy-backtest", response_model=MultiStrategyBacktestResponse)
async def run_multi_strategy_backtest(
    request: MultiStrategyBacktestRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_db)
) -> MultiStrategyBacktestResponse:
    """Run a multi-strategy portfolio backtest."""
    try:
        # Initialize multi-strategy backtester
        backtester = MultiStrategyBacktester()
        
        # Run backtest
        results = await backtester.run_multi_strategy_backtest(
            strategies=request.strategies,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            optimization_method=request.optimization_method,
            optimization_params=request.optimization_params,
            rebalance_frequency=request.rebalance_frequency,
            symbols=request.symbols
        )
        
        # Create backtest record in database
        async with uow:
            backtest = await uow.backtests.create({
                "name": request.name or f"Multi-Strategy Portfolio ({len(request.strategies)} strategies)",
                "description": request.description,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "initial_capital": request.initial_capital,
                "provider": "multi_strategy",
                "configuration": {
                    "optimization_method": request.optimization_method,
                    "optimization_params": request.optimization_params,
                    "rebalance_frequency": request.rebalance_frequency,
                    "strategy_count": len(request.strategies)
                },
                "created_by_id": current_user.id,
                "status": "completed",
                "total_return": results['total_return'],
                "annualized_return": results['annualized_return'],
                "volatility": results['volatility'],
                "sharpe_ratio": results['sharpe_ratio'],
                "sortino_ratio": results['sortino_ratio'],
                "max_drawdown": results['max_drawdown'],
                "win_rate": results['win_rate'],
                "equity_curve": results.get('equity_curve'),
                "trades": results.get('trades'),
                "statistics": {
                    "profit_factor": results.get('profit_factor', 0),
                    "total_trades": results.get('total_trades', 0),
                    "strategy_count": results.get('strategy_count', 0),
                    "strategies": results.get('strategies', [])
                }
            })
            await uow.commit()
            
        logger.info(
            "Multi-strategy backtest completed",
            user_id=current_user.id,
            backtest_id=backtest.id,
            strategy_count=len(request.strategies),
            total_return=results['total_return']
        )
        
        return MultiStrategyBacktestResponse(
            backtest_id=backtest.id,
            results=results,
            status="completed"
        )
        
    except Exception as e:
        logger.error(
            "Multi-strategy backtest failed",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-strategy backtest failed: {str(e)}"
        )


@router.post("/risk-metrics", response_model=RiskMetricsResponse)
async def calculate_risk_metrics(
    request: RiskMetricsRequest,
    current_user: User = Depends(get_current_user)
) -> RiskMetricsResponse:
    """Calculate comprehensive risk metrics for returns data."""
    try:
        # Create risk calculator
        calculator = RiskMetricsCalculator(
            returns=request.returns,
            benchmark_returns=request.benchmark_returns
        )
        
        # Calculate all metrics
        metrics = calculator.calculate_all_metrics(
            confidence_levels=request.confidence_levels or [0.95, 0.99]
        )
        
        logger.info(
            "Risk metrics calculated",
            user_id=current_user.id,
            metrics_count=len(metrics)
        )
        
        return RiskMetricsResponse(metrics=metrics)
        
    except Exception as e:
        logger.error(
            "Risk metrics calculation failed",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk metrics calculation failed: {str(e)}"
        )


@router.get("/optimization-methods")
async def get_optimization_methods(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get available portfolio optimization methods."""
    return {
        "methods": [
            {
                "id": "mean_variance",
                "name": "Mean-Variance (Markowitz)",
                "description": "Classic portfolio optimization minimizing risk for target return",
                "parameters": ["target_return", "constraints"]
            },
            {
                "id": "max_sharpe",
                "name": "Maximum Sharpe Ratio",
                "description": "Optimize for best risk-adjusted returns",
                "parameters": []
            },
            {
                "id": "min_volatility",
                "name": "Minimum Volatility",
                "description": "Find the lowest risk portfolio",
                "parameters": []
            },
            {
                "id": "risk_parity",
                "name": "Risk Parity",
                "description": "Equal risk contribution from each asset",
                "parameters": []
            },
            {
                "id": "black_litterman",
                "name": "Black-Litterman",
                "description": "Combine market equilibrium with investor views",
                "parameters": ["market_caps", "views", "view_confidence", "tau"]
            }
        ]
    }