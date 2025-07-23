"""Backtesting service implementation using backtesting.py library."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, Optional, Any
import json

import pandas as pd
from backtesting import Backtest
from backtesting._stats import compute_stats
import structlog

from core.config import settings
from models.backtest import BacktestStatus
from repositories.unit_of_work import UnitOfWork
from schemas.backtest import BacktestCreate, BacktestResultsUpload
from messaging.publisher import MessagePublisher
from messaging.backtest_schemas import BacktestMessage
from .strategies import StrategyFactory
from .data_loader import DataLoader

logger = structlog.get_logger(__name__)


class BacktestingService:
    """Service for running financial strategy backtests."""
    
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.executor = ThreadPoolExecutor(max_workers=settings.BACKTEST_WORKERS)
        self.data_loader = DataLoader()
        self.strategy_factory = StrategyFactory()
        self.publisher = MessagePublisher()
    
    async def create_and_run_backtest(
        self,
        backtest_data: BacktestCreate,
        user_id: int
    ) -> Dict[str, Any]:
        """Create a new backtest and run it asynchronously."""
        # Create backtest record
        async with self.uow:
            # Get strategy to validate it exists
            strategy = await self.uow.strategies.get(backtest_data.strategy_id)
            if not strategy:
                raise ValueError(f"Strategy {backtest_data.strategy_id} not found")
            
            # Create backtest entry
            backtest = await self.uow.backtests.create({
                "name": backtest_data.name,
                "description": backtest_data.description,
                "start_date": backtest_data.start_date,
                "end_date": backtest_data.end_date,
                "initial_capital": backtest_data.initial_capital,
                "provider": backtest_data.provider,
                "configuration": backtest_data.configuration,
                "strategy_id": backtest_data.strategy_id,
                "created_by_id": user_id,
                "status": BacktestStatus.QUEUED
            })
            await self.uow.commit()
            backtest_id = backtest.id
            
            logger.info(
                "Created backtest",
                backtest_id=backtest_id,
                strategy_id=backtest_data.strategy_id,
                user_id=user_id
            )
        
        # Publish message to RabbitMQ for async processing
        message = BacktestMessage(
            backtest_id=backtest_id,
            strategy_id=backtest_data.strategy_id,
            start_date=backtest_data.start_date,
            end_date=backtest_data.end_date,
            initial_capital=backtest_data.initial_capital,
            provider=backtest_data.provider,
            configuration=backtest_data.configuration
        )
        
        await self.publisher.publish_message(
            message=message.model_dump_json(),
            routing_key="backtest_processing"
        )
        
        logger.info(
            "Backtest queued for processing",
            backtest_id=backtest_id,
            strategy_id=backtest_data.strategy_id
        )
        
        return {"backtest_id": backtest_id, "status": "queued"}
    
    async def _run_backtest_async(self, backtest_id: int, strategy: Any) -> None:
        """Run backtest in background."""
        try:
            # Update status to running
            async with self.uow:
                await self.uow.backtests.update(
                    backtest_id,
                    {"status": BacktestStatus.RUNNING, "started_at": datetime.utcnow()}
                )
                await self.uow.commit()
            
            # Run backtest
            results = await self.run_backtest(backtest_id, strategy)
            
            # Update with results
            async with self.uow:
                await self.uow.backtests.update(
                    backtest_id,
                    {
                        "status": BacktestStatus.COMPLETED,
                        "completed_at": datetime.utcnow(),
                        **results
                    }
                )
                await self.uow.commit()
                
            logger.info("Backtest completed", backtest_id=backtest_id)
            
        except Exception as e:
            logger.error("Backtest failed", backtest_id=backtest_id, error=str(e))
            async with self.uow:
                await self.uow.backtests.update(
                    backtest_id,
                    {
                        "status": BacktestStatus.FAILED,
                        "completed_at": datetime.utcnow(),
                        "error_message": str(e)
                    }
                )
                await self.uow.commit()
    
    async def run_backtest(self, backtest_id: int, strategy: Any) -> Dict[str, Any]:
        """Execute the actual backtest using backtesting.py."""
        async with self.uow:
            backtest = await self.uow.backtests.get(backtest_id)
            if not backtest:
                raise ValueError(f"Backtest {backtest_id} not found")
        
        # Load historical data
        data = await self.data_loader.load_data(
            asset_class=strategy.asset_class,
            start_date=backtest.start_date,
            end_date=backtest.end_date,
            symbols=strategy.parameters.get("symbols", ["SPY"])  # Default to SPY
        )
        
        # Create strategy class from parameters
        strategy_class = self.strategy_factory.create_strategy(
            strategy_type=strategy.parameters.get("type", "sma_crossover"),
            parameters=strategy.parameters,
            entry_rules=strategy.entry_rules,
            exit_rules=strategy.exit_rules,
            risk_parameters=strategy.risk_parameters
        )
        
        # Run backtest in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(
            self.executor,
            self._execute_backtest,
            data,
            strategy_class,
            backtest.initial_capital,
            backtest.configuration.get("commission", 0.002),
            backtest.configuration.get("margin", 1.0),
            backtest.configuration.get("trade_on_close", True),
            backtest.configuration.get("hedging", False),
            backtest.configuration.get("exclusive_orders", True)
        )
        
        # Format results
        return self._format_results(stats)
    
    def _execute_backtest(
        self,
        data: pd.DataFrame,
        strategy_class: type,
        cash: float,
        commission: float,
        margin: float,
        trade_on_close: bool,
        hedging: bool,
        exclusive_orders: bool
    ) -> pd.Series:
        """Execute the backtest synchronously."""
        bt = Backtest(
            data,
            strategy_class,
            cash=cash,
            commission=commission,
            margin=margin,
            trade_on_close=trade_on_close,
            hedging=hedging,
            exclusive_orders=exclusive_orders
        )
        
        return bt.run()
    
    def _format_results(self, stats: pd.Series) -> Dict[str, Any]:
        """Format backtesting.py results for database storage."""
        # Extract equity curve data
        equity_curve = None
        if hasattr(stats, '_equity_curve'):
            equity_curve = {
                "dates": stats._equity_curve.index.astype(str).tolist(),
                "values": stats._equity_curve['Equity'].tolist()
            }
        
        # Extract trade data
        trades = None
        if hasattr(stats, '_trades') and stats._trades is not None:
            trades_df = stats._trades
            trades = {
                "count": len(trades_df),
                "data": trades_df.to_dict('records') if len(trades_df) > 0 else []
            }
        
        # Build statistics dictionary
        statistics = {
            "start": str(stats['Start']),
            "end": str(stats['End']),
            "duration": str(stats['Duration']),
            "exposure_time": float(stats['Exposure Time [%]']),
            "equity_final": float(stats['Equity Final [$]']),
            "equity_peak": float(stats['Equity Peak [$]']),
            "trades": int(stats['# Trades']),
            "profit_factor": float(stats.get('Profit Factor', 0) or 0),
            "expectancy": float(stats.get('Expectancy [%]', 0) or 0),
            "sqn": float(stats.get('SQN', 0) or 0)
        }
        
        return {
            "total_return": float(stats['Return [%]']),
            "annualized_return": float(stats.get('Return (Ann.) [%]', 0) or 0),
            "volatility": float(stats.get('Volatility (Ann.) [%]', 0) or 0),
            "sharpe_ratio": float(stats.get('Sharpe Ratio', 0) or 0),
            "sortino_ratio": float(stats.get('Sortino Ratio', 0) or 0),
            "max_drawdown": float(stats['Max. Drawdown [%]']),
            "win_rate": float(stats.get('Win Rate [%]', 0) or 0),
            "equity_curve": equity_curve,
            "trades": trades,
            "statistics": statistics
        }
    
    async def get_backtest_results(self, backtest_id: int) -> Optional[Dict[str, Any]]:
        """Get backtest results by ID."""
        async with self.uow:
            backtest = await self.uow.backtests.get(backtest_id)
            if not backtest:
                return None
                
            return {
                "id": backtest.id,
                "name": backtest.name,
                "status": backtest.status,
                "started_at": backtest.started_at,
                "completed_at": backtest.completed_at,
                "error_message": backtest.error_message,
                "results": {
                    "total_return": backtest.total_return,
                    "annualized_return": backtest.annualized_return,
                    "volatility": backtest.volatility,
                    "sharpe_ratio": backtest.sharpe_ratio,
                    "sortino_ratio": backtest.sortino_ratio,
                    "max_drawdown": backtest.max_drawdown,
                    "win_rate": backtest.win_rate
                },
                "equity_curve": backtest.equity_curve,
                "trades": backtest.trades,
                "statistics": backtest.statistics
            }
    
    def __del__(self):
        """Clean up thread pool on deletion."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)