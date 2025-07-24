"""Unit tests for multi-strategy portfolio backtesting."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from services.backtesting.multi_strategy import (
    MultiStrategyPortfolio,
    MultiStrategyBacktester
)
from services.backtesting.strategies import BaseStrategy


class MockStrategy(BaseStrategy):
    """Mock strategy for testing."""
    
    def init(self):
        """Initialize mock strategy."""
        self.initialized = True
    
    def next(self):
        """Mock next method."""
        pass


class TestMultiStrategyPortfolio:
    """Test suite for MultiStrategyPortfolio."""
    
    @pytest.fixture
    def portfolio(self):
        """Create a MultiStrategyPortfolio instance."""
        return MultiStrategyPortfolio()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample market data."""
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        data = pd.DataFrame({
            'Open': np.random.uniform(100, 110, 100),
            'High': np.random.uniform(110, 120, 100),
            'Low': np.random.uniform(90, 100, 100),
            'Close': np.random.uniform(95, 115, 100),
            'Volume': np.random.randint(1000000, 5000000, 100)
        }, index=dates)
        return data
    
    def test_initialization(self, portfolio):
        """Test portfolio initialization."""
        assert portfolio.strategies == []
        assert portfolio.weights == []
        assert portfolio.rebalance_frequency == 'monthly'
        assert portfolio.optimization_method == 'equal_weight'
        assert portfolio.optimization_params == {}
        assert portfolio.last_rebalance is None
        assert portfolio.current_positions == {}
    
    def test_add_strategy(self, portfolio):
        """Test adding strategies to portfolio."""
        strategy1 = MockStrategy()
        strategy2 = MockStrategy()
        
        portfolio.add_strategy(strategy1, weight=0.6)
        assert len(portfolio.strategies) == 1
        assert portfolio.weights == [0.6]
        
        portfolio.add_strategy(strategy2, weight=0.4)
        assert len(portfolio.strategies) == 2
        assert portfolio.weights == [0.6, 0.4]
        
        # Test equal weight default
        portfolio.strategies = []
        portfolio.weights = []
        
        portfolio.add_strategy(strategy1)
        portfolio.add_strategy(strategy2)
        assert portfolio.weights == [0.5, 0.5]
    
    def test_set_optimization_method(self, portfolio):
        """Test setting optimization method."""
        params = {'lookback_days': 60, 'risk_free_rate': 0.02}
        portfolio.set_optimization_method('mean_variance', params)
        
        assert portfolio.optimization_method == 'mean_variance'
        assert portfolio.optimization_params == params
    
    def test_should_rebalance(self, portfolio):
        """Test rebalancing frequency logic."""
        # Test daily rebalancing
        portfolio.rebalance_frequency = 'daily'
        portfolio.last_rebalance = datetime.now() - timedelta(days=1)
        assert portfolio._should_rebalance(datetime.now()) is True
        
        # Test weekly rebalancing
        portfolio.rebalance_frequency = 'weekly'
        portfolio.last_rebalance = datetime.now() - timedelta(days=6)
        assert portfolio._should_rebalance(datetime.now()) is False
        
        portfolio.last_rebalance = datetime.now() - timedelta(days=7)
        assert portfolio._should_rebalance(datetime.now()) is True
        
        # Test monthly rebalancing
        portfolio.rebalance_frequency = 'monthly'
        portfolio.last_rebalance = datetime.now().replace(day=1)
        current_date = portfolio.last_rebalance + timedelta(days=32)
        assert portfolio._should_rebalance(current_date) is True
    
    def test_get_strategy_signal(self, portfolio):
        """Test strategy signal extraction."""
        strategy = MockStrategy()
        
        # Test with no position
        signal = portfolio._get_strategy_signal(strategy)
        assert signal == 0.0
        
        # Test with position
        strategy.position = Mock()
        strategy.position.is_long = True
        signal = portfolio._get_strategy_signal(strategy)
        assert signal == 1.0
        
        strategy.position.is_long = False
        signal = portfolio._get_strategy_signal(strategy)
        assert signal == -1.0
    
    def test_combine_signals(self, portfolio):
        """Test signal combination logic."""
        portfolio.weights = [0.5, 0.3, 0.2]
        signals = [1.0, -1.0, 0.0]
        
        combined = portfolio._combine_signals(signals)
        expected = 0.5 * 1.0 + 0.3 * (-1.0) + 0.2 * 0.0
        assert combined == expected
    
    def test_rebalance_portfolio_equal_weight(self, portfolio):
        """Test equal weight rebalancing."""
        portfolio.strategies = [MockStrategy(), MockStrategy(), MockStrategy()]
        portfolio.optimization_method = 'equal_weight'
        
        portfolio._rebalance_portfolio()
        
        assert portfolio.weights == [1/3, 1/3, 1/3]


class TestMultiStrategyBacktester:
    """Test suite for MultiStrategyBacktester."""
    
    @pytest.fixture
    def backtester(self):
        """Create MultiStrategyBacktester instance."""
        return MultiStrategyBacktester()
    
    @pytest.fixture
    def strategy_configs(self):
        """Create sample strategy configurations."""
        return [
            {
                'type': 'sma_crossover',
                'parameters': {'fast_period': 10, 'slow_period': 20},
                'risk_parameters': {'position_size': 0.95}
            },
            {
                'type': 'rsi_mean_reversion',
                'parameters': {'rsi_period': 14},
                'risk_parameters': {'position_size': 0.95}
            }
        ]
    
    @pytest.mark.asyncio
    async def test_run_multi_strategy_backtest(self, backtester, strategy_configs):
        """Test running multi-strategy backtest."""
        # Mock data loader
        mock_data = pd.DataFrame({
            'Open': [100] * 100,
            'High': [105] * 100,
            'Low': [95] * 100,
            'Close': [102] * 100,
            'Volume': [1000000] * 100
        }, index=pd.date_range(start='2023-01-01', periods=100))
        
        with patch.object(backtester.data_loader, 'load_data', 
                         new_callable=AsyncMock) as mock_load:
            mock_load.return_value = mock_data
            
            # Mock backtest execution
            mock_stats = pd.Series({
                'Return [%]': 15.5,
                'Return (Ann.) [%]': 18.2,
                'Volatility (Ann.) [%]': 12.5,
                'Sharpe Ratio': 1.45,
                'Sortino Ratio': 1.85,
                'Max. Drawdown [%]': -8.5,
                'Win Rate [%]': 55.0,
                'Profit Factor': 1.8,
                '# Trades': 42
            })
            
            with patch.object(backtester, '_execute_multi_strategy_backtest',
                            return_value=mock_stats):
                
                results = await backtester.run_multi_strategy_backtest(
                    strategies=strategy_configs,
                    start_date=datetime(2023, 1, 1),
                    end_date=datetime(2023, 12, 31),
                    initial_capital=10000,
                    optimization_method='risk_parity',
                    rebalance_frequency='monthly'
                )
                
                assert results['total_return'] == 15.5
                assert results['sharpe_ratio'] == 1.45
                assert results['strategy_count'] == 2
                assert len(results['strategies']) == 2
    
    def test_format_multi_strategy_results(self, backtester, strategy_configs):
        """Test results formatting."""
        mock_stats = pd.Series({
            'Return [%]': 20.0,
            'Return (Ann.) [%]': 25.0,
            'Volatility (Ann.) [%]': 15.0,
            'Sharpe Ratio': 1.67,
            'Sortino Ratio': 2.1,
            'Max. Drawdown [%]': -10.0,
            'Win Rate [%]': 60.0,
            'Profit Factor': 2.0,
            '# Trades': 50
        })
        
        results = backtester._format_multi_strategy_results(mock_stats, strategy_configs)
        
        assert results['total_return'] == 20.0
        assert results['annualized_return'] == 25.0
        assert results['volatility'] == 15.0
        assert results['sharpe_ratio'] == 1.67
        assert results['sortino_ratio'] == 2.1
        assert results['max_drawdown'] == -10.0
        assert results['win_rate'] == 60.0
        assert results['profit_factor'] == 2.0
        assert results['total_trades'] == 50
        assert results['strategy_count'] == 2
        assert results['strategies'] == ['sma_crossover', 'rsi_mean_reversion']
    
    @pytest.mark.asyncio
    async def test_error_handling(self, backtester, strategy_configs):
        """Test error handling in multi-strategy backtest."""
        # Mock data loader to raise error
        with patch.object(backtester.data_loader, 'load_data',
                         side_effect=Exception("Data loading failed")):
            
            with pytest.raises(Exception) as exc_info:
                await backtester.run_multi_strategy_backtest(
                    strategies=strategy_configs,
                    start_date=datetime(2023, 1, 1),
                    end_date=datetime(2023, 12, 31),
                    initial_capital=10000
                )
            
            assert "Data loading failed" in str(exc_info.value)