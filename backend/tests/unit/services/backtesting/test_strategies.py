"""Tests for backtesting strategies."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backtesting import Backtest

from services.backtesting.strategies import (
    StrategyFactory,
    SMACrossoverStrategy,
    RSIMeanReversionStrategy,
    BollingerBandsStrategy,
    MomentumStrategy
)


class TestStrategyFactory:
    """Test the strategy factory."""
    
    def test_create_sma_crossover_strategy(self):
        """Test creating SMA crossover strategy."""
        factory = StrategyFactory()
        
        strategy_class = factory.create_strategy(
            strategy_type="sma_crossover",
            parameters={"fast_period": 10, "slow_period": 20},
            entry_rules={},
            exit_rules={},
            risk_parameters={"position_size": 0.95}
        )
        
        # Verify it's a proper strategy class
        assert issubclass(strategy_class, SMACrossoverStrategy)
        
        # Create instance and verify parameters
        instance = strategy_class()
        assert instance.parameters["fast_period"] == 10
        assert instance.parameters["slow_period"] == 20
        assert instance.risk_parameters["position_size"] == 0.95
    
    def test_create_rsi_strategy(self):
        """Test creating RSI strategy."""
        factory = StrategyFactory()
        
        strategy_class = factory.create_strategy(
            strategy_type="rsi_mean_reversion",
            parameters={
                "rsi_period": 14,
                "oversold_level": 30,
                "overbought_level": 70
            },
            entry_rules={},
            exit_rules={},
            risk_parameters={"position_size": 0.5}
        )
        
        assert issubclass(strategy_class, RSIMeanReversionStrategy)
    
    def test_create_bollinger_bands_strategy(self):
        """Test creating Bollinger Bands strategy."""
        factory = StrategyFactory()
        
        strategy_class = factory.create_strategy(
            strategy_type="bollinger_bands",
            parameters={"bb_period": 20, "bb_std": 2},
            entry_rules={},
            exit_rules={},
            risk_parameters={"position_size": 0.8}
        )
        
        assert issubclass(strategy_class, BollingerBandsStrategy)
    
    def test_create_momentum_strategy(self):
        """Test creating momentum strategy."""
        factory = StrategyFactory()
        
        strategy_class = factory.create_strategy(
            strategy_type="momentum",
            parameters={"lookback_period": 20, "threshold": 0.05},
            entry_rules={},
            exit_rules={},
            risk_parameters={"position_size": 1.0}
        )
        
        assert issubclass(strategy_class, MomentumStrategy)
    
    def test_invalid_strategy_type(self):
        """Test creating strategy with invalid type."""
        factory = StrategyFactory()
        
        with pytest.raises(ValueError, match="Unknown strategy type"):
            factory.create_strategy(
                strategy_type="invalid_strategy",
                parameters={},
                entry_rules={},
                exit_rules={},
                risk_parameters={}
            )
    
    def test_list_available_strategies(self):
        """Test listing available strategies."""
        factory = StrategyFactory()
        strategies = factory.list_available_strategies()
        
        assert isinstance(strategies, list)
        assert "sma_crossover" in strategies
        assert "rsi_mean_reversion" in strategies
        assert "bollinger_bands" in strategies
        assert "momentum" in strategies
        assert "custom" in strategies


class TestSMACrossoverStrategy:
    """Test SMA crossover strategy execution."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        np.random.seed(42)
        
        # Generate trending price data
        trend = np.linspace(100, 120, 100)
        noise = np.random.normal(0, 1, 100)
        prices = trend + noise
        
        data = pd.DataFrame({
            "Open": prices * 0.99,
            "High": prices * 1.01,
            "Low": prices * 0.98,
            "Close": prices,
            "Volume": np.random.randint(1000000, 2000000, 100)
        }, index=dates)
        
        return data
    
    def test_sma_crossover_backtest(self, sample_data):
        """Test running a backtest with SMA crossover strategy."""
        factory = StrategyFactory()
        
        strategy_class = factory.create_strategy(
            strategy_type="sma_crossover",
            parameters={"fast_period": 5, "slow_period": 10},
            entry_rules={},
            exit_rules={},
            risk_parameters={"position_size": 0.95}
        )
        
        # Run backtest
        bt = Backtest(
            sample_data,
            strategy_class,
            cash=10000,
            commission=0.002
        )
        
        stats = bt.run()
        
        # Verify backtest ran successfully
        assert stats is not None
        assert "Return [%]" in stats
        assert "Sharpe Ratio" in stats
        assert "Max. Drawdown [%]" in stats
        assert stats["# Trades"] >= 0


class TestRSIMeanReversionStrategy:
    """Test RSI mean reversion strategy."""
    
    @pytest.fixture
    def oscillating_data(self):
        """Create oscillating price data for mean reversion testing."""
        dates = pd.date_range(start="2023-01-01", periods=200, freq="D")
        
        # Generate oscillating price data
        t = np.linspace(0, 20, 200)
        prices = 100 + 10 * np.sin(t) + np.random.normal(0, 0.5, 200)
        
        data = pd.DataFrame({
            "Open": prices * 0.995,
            "High": prices * 1.005,
            "Low": prices * 0.99,
            "Close": prices,
            "Volume": np.random.randint(500000, 1500000, 200)
        }, index=dates)
        
        return data
    
    def test_rsi_strategy_backtest(self, oscillating_data):
        """Test RSI strategy on oscillating data."""
        factory = StrategyFactory()
        
        strategy_class = factory.create_strategy(
            strategy_type="rsi_mean_reversion",
            parameters={
                "rsi_period": 14,
                "oversold_level": 30,
                "overbought_level": 70
            },
            entry_rules={},
            exit_rules={},
            risk_parameters={"position_size": 0.5}
        )
        
        bt = Backtest(
            oscillating_data,
            strategy_class,
            cash=10000,
            commission=0.002
        )
        
        stats = bt.run()
        
        assert stats is not None
        assert stats["# Trades"] > 0  # Should have trades in oscillating market