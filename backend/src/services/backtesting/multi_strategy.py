"""Multi-strategy portfolio backtesting implementation.

This module allows running multiple strategies simultaneously and combining
their signals using portfolio optimization techniques.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import structlog

from backtesting import Backtest, Strategy
from backtesting.lib import crossover

from .strategies import StrategyFactory, BaseStrategy
from .portfolio_optimizer import PortfolioOptimizer
from .data_loader import DataLoader

logger = structlog.get_logger(__name__)


class MultiStrategyPortfolio(Strategy):
    """Strategy that combines multiple sub-strategies using portfolio weights."""
    
    def __init__(self):
        super().__init__()
        self.strategies = []
        self.weights = []
        self.rebalance_frequency = 'monthly'
        self.optimization_method = 'equal_weight'
        self.optimization_params = {}
        self.last_rebalance = None
        self.current_positions = {}
        
    def add_strategy(self, strategy: BaseStrategy, weight: float = None):
        """Add a strategy to the portfolio."""
        self.strategies.append(strategy)
        if weight is not None:
            self.weights.append(weight)
        else:
            # Equal weight by default
            self.weights = [1/len(self.strategies)] * len(self.strategies)
            
    def set_optimization_method(self, method: str, params: Dict[str, Any] = None):
        """Set the portfolio optimization method."""
        self.optimization_method = method
        self.optimization_params = params or {}
        
    def init(self):
        """Initialize all sub-strategies."""
        # Initialize each strategy
        for strategy in self.strategies:
            # Share the same data with sub-strategies
            strategy.data = self.data
            strategy._broker = self._broker
            strategy.init()
            
        # Initialize rebalancing
        self.last_rebalance = self.data.index[0]
        
    def next(self):
        """Execute portfolio logic on each bar."""
        current_date = self.data.index[-1]
        
        # Check if we need to rebalance
        should_rebalance = self._should_rebalance(current_date)
        
        if should_rebalance:
            self._rebalance_portfolio()
            self.last_rebalance = current_date
            
        # Execute each strategy's logic
        strategy_signals = []
        for i, strategy in enumerate(self.strategies):
            # Get strategy signal
            signal = self._get_strategy_signal(strategy)
            strategy_signals.append(signal)
            
        # Combine signals based on weights
        combined_signal = self._combine_signals(strategy_signals)
        
        # Execute trades based on combined signal
        self._execute_portfolio_trades(combined_signal)
        
    def _should_rebalance(self, current_date: pd.Timestamp) -> bool:
        """Check if portfolio should be rebalanced."""
        if self.last_rebalance is None:
            return True
            
        if self.rebalance_frequency == 'daily':
            return True
        elif self.rebalance_frequency == 'weekly':
            return (current_date - self.last_rebalance).days >= 7
        elif self.rebalance_frequency == 'monthly':
            return current_date.month != self.last_rebalance.month
        elif self.rebalance_frequency == 'quarterly':
            return current_date.quarter != self.last_rebalance.quarter
        elif self.rebalance_frequency == 'yearly':
            return current_date.year != self.last_rebalance.year
        else:
            return False
            
    def _rebalance_portfolio(self):
        """Rebalance portfolio weights using specified optimization method."""
        if self.optimization_method == 'equal_weight':
            self.weights = [1/len(self.strategies)] * len(self.strategies)
            
        elif self.optimization_method in ['mean_variance', 'sharpe', 'min_volatility']:
            # Get historical returns for each strategy
            lookback = self.optimization_params.get('lookback_days', 60)
            returns = self._get_strategy_returns(lookback)
            
            if returns is not None and len(returns) > 10:
                optimizer = PortfolioOptimizer(
                    returns,
                    risk_free_rate=self.optimization_params.get('risk_free_rate', 0.02)
                )
                
                if self.optimization_method == 'mean_variance':
                    result = optimizer.mean_variance_optimization(
                        target_return=self.optimization_params.get('target_return')
                    )
                elif self.optimization_method == 'sharpe':
                    result = optimizer.maximum_sharpe_portfolio()
                else:  # min_volatility
                    result = optimizer.minimum_volatility_portfolio()
                    
                if result['success']:
                    # Update weights
                    self.weights = [
                        result['weights'].get(f'strategy_{i}', 0)
                        for i in range(len(self.strategies))
                    ]
                    
        elif self.optimization_method == 'risk_parity':
            lookback = self.optimization_params.get('lookback_days', 60)
            returns = self._get_strategy_returns(lookback)
            
            if returns is not None and len(returns) > 10:
                optimizer = PortfolioOptimizer(returns)
                result = optimizer.risk_parity()
                
                if result['success']:
                    self.weights = [
                        result['weights'].get(f'strategy_{i}', 0)
                        for i in range(len(self.strategies))
                    ]
                    
    def _get_strategy_returns(self, lookback_days: int) -> Optional[pd.DataFrame]:
        """Calculate historical returns for each strategy."""
        # This is a simplified version - in production, you'd track
        # actual strategy performance over time
        try:
            end_idx = len(self.data)
            start_idx = max(0, end_idx - lookback_days)
            
            if start_idx >= end_idx:
                return None
                
            # For now, use price returns as proxy
            # In production, track actual strategy returns
            price_data = self.data.Close[start_idx:end_idx]
            returns = price_data.pct_change().dropna()
            
            # Create DataFrame with strategy returns
            # This is simplified - each strategy would have different returns
            strategy_returns = pd.DataFrame()
            for i in range(len(self.strategies)):
                # Add some randomness to differentiate strategies
                # In production, track actual strategy P&L
                noise = np.random.normal(0, 0.001, len(returns))
                strategy_returns[f'strategy_{i}'] = returns + noise
                
            return strategy_returns
            
        except Exception as e:
            logger.error("Error calculating strategy returns", error=str(e))
            return None
            
    def _get_strategy_signal(self, strategy: BaseStrategy) -> float:
        """Get trading signal from a strategy (-1 to 1)."""
        # This would need to be implemented based on strategy type
        # For now, return a simple signal based on position
        if hasattr(strategy, 'position') and strategy.position:
            return 1.0 if strategy.position.is_long else -1.0
        return 0.0
        
    def _combine_signals(self, signals: List[float]) -> float:
        """Combine multiple strategy signals into portfolio signal."""
        # Weighted average of signals
        weighted_sum = sum(s * w for s, w in zip(signals, self.weights))
        return weighted_sum
        
    def _execute_portfolio_trades(self, signal: float):
        """Execute trades based on combined signal."""
        # Simple threshold-based execution
        threshold = self.optimization_params.get('signal_threshold', 0.3)
        
        if signal > threshold and not self.position:
            # Buy signal
            self.buy(size=self.optimization_params.get('position_size', 0.95))
        elif signal < -threshold and self.position:
            # Sell signal
            self.position.close()


class MultiStrategyBacktester:
    """Service for running multi-strategy portfolio backtests."""
    
    def __init__(self):
        self.strategy_factory = StrategyFactory()
        self.data_loader = DataLoader()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def run_multi_strategy_backtest(
        self,
        strategies: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        optimization_method: str = 'equal_weight',
        optimization_params: Optional[Dict[str, Any]] = None,
        rebalance_frequency: str = 'monthly',
        symbols: List[str] = None
    ) -> Dict[str, Any]:
        """Run a multi-strategy portfolio backtest.
        
        Args:
            strategies: List of strategy configurations
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital
            optimization_method: Portfolio optimization method
            optimization_params: Parameters for optimization
            rebalance_frequency: How often to rebalance
            symbols: List of symbols to trade
            
        Returns:
            Dict with backtest results
        """
        try:
            # Load data for all required symbols
            all_symbols = set()
            for strategy_config in strategies:
                strategy_symbols = strategy_config.get('symbols', ['SPY'])
                all_symbols.update(strategy_symbols)
                
            if symbols:
                all_symbols.update(symbols)
                
            # Load data
            data_dict = {}
            for symbol in all_symbols:
                data = await self.data_loader.load_data(
                    asset_class='equity',  # Default to equity
                    start_date=start_date,
                    end_date=end_date,
                    symbols=[symbol]
                )
                data_dict[symbol] = data
                
            # Use the first symbol's data as the main data
            # In production, you might want to merge or handle multiple symbols differently
            main_symbol = list(all_symbols)[0]
            main_data = data_dict[main_symbol]
            
            # Create multi-strategy portfolio
            portfolio = MultiStrategyPortfolio()
            portfolio.set_optimization_method(
                optimization_method,
                optimization_params or {}
            )
            portfolio.rebalance_frequency = rebalance_frequency
            
            # Add each strategy to portfolio
            for strategy_config in strategies:
                strategy_type = strategy_config.get('type', 'sma_crossover')
                strategy_class = self.strategy_factory.create_strategy(
                    strategy_type=strategy_type,
                    parameters=strategy_config.get('parameters', {}),
                    entry_rules=strategy_config.get('entry_rules', {}),
                    exit_rules=strategy_config.get('exit_rules', {}),
                    risk_parameters=strategy_config.get('risk_parameters', {})
                )
                
                # Create instance and add to portfolio
                strategy_instance = strategy_class()
                portfolio.add_strategy(strategy_instance)
                
            # Run backtest
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(
                self.executor,
                self._execute_multi_strategy_backtest,
                main_data,
                portfolio,
                initial_capital
            )
            
            # Format results
            results = self._format_multi_strategy_results(stats, strategies)
            
            return results
            
        except Exception as e:
            logger.error(
                "Multi-strategy backtest failed",
                error=str(e),
                strategies=len(strategies)
            )
            raise
            
    def _execute_multi_strategy_backtest(
        self,
        data: pd.DataFrame,
        portfolio: MultiStrategyPortfolio,
        initial_capital: float
    ) -> pd.Series:
        """Execute the multi-strategy backtest."""
        bt = Backtest(
            data,
            portfolio,
            cash=initial_capital,
            commission=0.002,
            exclusive_orders=True
        )
        
        return bt.run()
        
    def _format_multi_strategy_results(
        self,
        stats: pd.Series,
        strategies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Format multi-strategy backtest results."""
        # Basic results formatting
        results = {
            'total_return': float(stats['Return [%]']),
            'annualized_return': float(stats.get('Return (Ann.) [%]', 0) or 0),
            'volatility': float(stats.get('Volatility (Ann.) [%]', 0) or 0),
            'sharpe_ratio': float(stats.get('Sharpe Ratio', 0) or 0),
            'sortino_ratio': float(stats.get('Sortino Ratio', 0) or 0),
            'max_drawdown': float(stats['Max. Drawdown [%]']),
            'win_rate': float(stats.get('Win Rate [%]', 0) or 0),
            'profit_factor': float(stats.get('Profit Factor', 0) or 0),
            'total_trades': int(stats['# Trades']),
            'strategy_count': len(strategies),
            'strategies': [s.get('type', 'unknown') for s in strategies]
        }
        
        # Add equity curve if available
        if hasattr(stats, '_equity_curve'):
            results['equity_curve'] = {
                'dates': stats._equity_curve.index.astype(str).tolist(),
                'values': stats._equity_curve['Equity'].tolist()
            }
            
        # Add trade data if available
        if hasattr(stats, '_trades') and stats._trades is not None:
            trades_df = stats._trades
            results['trades'] = {
                'count': len(trades_df),
                'data': trades_df.to_dict('records') if len(trades_df) > 0 else []
            }
            
        return results