"""Tests for backtesting service."""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, AsyncMock, patch
import pandas as pd
import numpy as np

from services.backtesting.service import BacktestingService
from models.backtest import BacktestStatus, BacktestProvider
from schemas.backtest import BacktestCreate


@pytest.mark.asyncio
class TestBacktestingService:
    """Test the backtesting service."""
    
    @pytest.fixture
    def mock_uow(self):
        """Create mock unit of work."""
        uow = AsyncMock()
        
        # Mock repositories
        uow.strategies = AsyncMock()
        uow.backtests = AsyncMock()
        
        # Mock commit
        uow.commit = AsyncMock()
        
        # Make it work as async context manager
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        
        return uow
    
    @pytest.fixture
    def mock_strategy(self):
        """Create mock strategy."""
        strategy = Mock()
        strategy.id = 1
        strategy.name = "Test Strategy"
        strategy.asset_class = "EQUITY"
        strategy.parameters = {
            "type": "sma_crossover",
            "symbols": ["SPY"],
            "fast_period": 10,
            "slow_period": 20
        }
        strategy.entry_rules = {}
        strategy.exit_rules = {}
        strategy.risk_parameters = {"position_size": 0.95}
        return strategy
    
    @pytest.fixture
    def mock_backtest(self):
        """Create mock backtest."""
        backtest = Mock()
        backtest.id = 1
        backtest.name = "Test Backtest"
        backtest.start_date = date(2023, 1, 1)
        backtest.end_date = date(2023, 12, 31)
        backtest.initial_capital = 10000
        backtest.configuration = {"commission": 0.002}
        return backtest
    
    @pytest.fixture
    def backtest_create_data(self):
        """Create backtest creation data."""
        return BacktestCreate(
            name="Test Backtest",
            description="Test backtest description",
            strategy_id=1,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            initial_capital=10000,
            provider=BacktestProvider.CUSTOM,
            configuration={"commission": 0.002}
        )
    
    @pytest.fixture
    def mock_market_data(self):
        """Create mock market data."""
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        prices = 100 + np.cumsum(np.random.randn(100))
        
        return pd.DataFrame({
            "Open": prices * 0.99,
            "High": prices * 1.01,
            "Low": prices * 0.98,
            "Close": prices,
            "Volume": np.random.randint(1000000, 2000000, 100)
        }, index=dates)
    
    @pytest.fixture
    def mock_stats(self):
        """Create mock backtest statistics."""
        stats = pd.Series({
            "Return [%]": 15.5,
            "Return (Ann.) [%]": 16.2,
            "Volatility (Ann.) [%]": 12.5,
            "Sharpe Ratio": 1.3,
            "Sortino Ratio": 1.8,
            "Max. Drawdown [%]": -8.5,
            "Win Rate [%]": 55.0,
            "# Trades": 25,
            "Start": pd.Timestamp("2023-01-01"),
            "End": pd.Timestamp("2023-12-31"),
            "Duration": pd.Timedelta(days=365),
            "Exposure Time [%]": 85.0,
            "Equity Final [$]": 11550,
            "Equity Peak [$]": 11800,
            "Profit Factor": 1.5,
            "Expectancy [%]": 0.62,
            "SQN": 2.1
        })
        return stats
    
    @patch("services.backtesting.service.MessagePublisher")
    async def test_create_and_run_backtest(
        self, 
        mock_publisher_class,
        mock_uow, 
        mock_strategy, 
        backtest_create_data
    ):
        """Test creating and queuing a backtest."""
        # Setup mocks
        mock_publisher = AsyncMock()
        mock_publisher_class.return_value = mock_publisher
        
        mock_uow.strategies.get.return_value = mock_strategy
        
        # Mock backtest creation
        created_backtest = Mock()
        created_backtest.id = 1
        mock_uow.backtests.create.return_value = created_backtest
        
        # Create service
        service = BacktestingService(mock_uow)
        
        # Run test
        result = await service.create_and_run_backtest(backtest_create_data, user_id=1)
        
        # Verify
        assert result["backtest_id"] == 1
        assert result["status"] == "queued"
        
        # Verify strategy was fetched
        mock_uow.strategies.get.assert_called_once_with(1)
        
        # Verify backtest was created
        mock_uow.backtests.create.assert_called_once()
        create_args = mock_uow.backtests.create.call_args[0][0]
        assert create_args["name"] == "Test Backtest"
        assert create_args["status"] == BacktestStatus.QUEUED
        assert create_args["created_by_id"] == 1
        
        # Verify message was published
        mock_publisher.publish_message.assert_called_once()
        publish_args = mock_publisher.publish_message.call_args
        assert publish_args.kwargs["routing_key"] == "backtest_processing"
        
        # Verify commit was called
        mock_uow.commit.assert_called()
    
    async def test_create_backtest_strategy_not_found(
        self, 
        mock_uow, 
        backtest_create_data
    ):
        """Test creating backtest with non-existent strategy."""
        # Setup mocks
        mock_uow.strategies.get.return_value = None
        
        # Create service
        service = BacktestingService(mock_uow)
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="Strategy 1 not found"):
            await service.create_and_run_backtest(backtest_create_data, user_id=1)
    
    @patch("services.backtesting.service.DataLoader")
    @patch("services.backtesting.service.StrategyFactory")
    async def test_run_backtest(
        self,
        mock_factory_class,
        mock_loader_class,
        mock_uow,
        mock_strategy,
        mock_backtest,
        mock_market_data,
        mock_stats
    ):
        """Test running a backtest."""
        # Setup mocks
        mock_loader = AsyncMock()
        mock_loader.load_data.return_value = mock_market_data
        mock_loader_class.return_value = mock_loader
        
        mock_factory = Mock()
        mock_strategy_class = Mock()
        mock_factory.create_strategy.return_value = mock_strategy_class
        mock_factory_class.return_value = mock_factory
        
        mock_uow.backtests.get.return_value = mock_backtest
        
        # Create service
        service = BacktestingService(mock_uow)
        
        # Mock the backtest execution
        with patch.object(service, "_execute_backtest", return_value=mock_stats):
            results = await service.run_backtest(1, mock_strategy)
        
        # Verify results
        assert results["total_return"] == 15.5
        assert results["sharpe_ratio"] == 1.3
        assert results["max_drawdown"] == -8.5
        assert results["win_rate"] == 55.0
        
        # Verify data was loaded
        mock_loader.load_data.assert_called_once_with(
            asset_class="EQUITY",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            symbols=["SPY"]
        )
        
        # Verify strategy was created
        mock_factory.create_strategy.assert_called_once_with(
            strategy_type="sma_crossover",
            parameters=mock_strategy.parameters,
            entry_rules={},
            exit_rules={},
            risk_parameters={"position_size": 0.95}
        )
    
    def test_format_results(self, mock_stats):
        """Test formatting backtest results."""
        service = BacktestingService(Mock())
        
        # Add mock equity curve
        mock_stats._equity_curve = pd.DataFrame({
            "Equity": [10000, 10500, 11000, 11550]
        }, index=pd.date_range("2023-01-01", periods=4))
        
        # Add mock trades
        mock_stats._trades = pd.DataFrame({
            "Size": [100, -100, 50],
            "EntryPrice": [100, 105, 110],
            "ExitPrice": [105, 100, 115],
            "PnL": [500, 500, 250]
        })
        
        # Format results
        results = service._format_results(mock_stats)
        
        # Verify basic metrics
        assert results["total_return"] == 15.5
        assert results["annualized_return"] == 16.2
        assert results["volatility"] == 12.5
        assert results["sharpe_ratio"] == 1.3
        assert results["sortino_ratio"] == 1.8
        assert results["max_drawdown"] == -8.5
        assert results["win_rate"] == 55.0
        
        # Verify equity curve
        assert results["equity_curve"] is not None
        assert len(results["equity_curve"]["values"]) == 4
        assert results["equity_curve"]["values"][-1] == 11550
        
        # Verify trades
        assert results["trades"] is not None
        assert results["trades"]["count"] == 3
        assert len(results["trades"]["data"]) == 3
        
        # Verify statistics
        assert results["statistics"] is not None
        assert results["statistics"]["trades"] == 25
        assert results["statistics"]["profit_factor"] == 1.5
    
    async def test_get_backtest_results(self, mock_uow, mock_backtest):
        """Test getting backtest results."""
        # Setup mock
        mock_backtest.status = BacktestStatus.COMPLETED
        mock_backtest.total_return = 15.5
        mock_backtest.sharpe_ratio = 1.3
        mock_backtest.max_drawdown = -8.5
        mock_backtest.equity_curve = {"dates": [], "values": []}
        mock_backtest.trades = {"count": 25}
        mock_backtest.statistics = {"exposure_time": 85.0}
        
        mock_uow.backtests.get.return_value = mock_backtest
        
        # Create service
        service = BacktestingService(mock_uow)
        
        # Get results
        results = await service.get_backtest_results(1)
        
        # Verify
        assert results is not None
        assert results["id"] == 1
        assert results["status"] == BacktestStatus.COMPLETED
        assert results["results"]["total_return"] == 15.5
        assert results["results"]["sharpe_ratio"] == 1.3
        assert results["equity_curve"] == {"dates": [], "values": []}
    
    async def test_get_backtest_results_not_found(self, mock_uow):
        """Test getting results for non-existent backtest."""
        mock_uow.backtests.get.return_value = None
        
        service = BacktestingService(mock_uow)
        results = await service.get_backtest_results(999)
        
        assert results is None