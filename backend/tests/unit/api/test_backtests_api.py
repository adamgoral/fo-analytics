"""Tests for backtest API endpoints."""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, AsyncMock, patch
from fastapi import status

from models.backtest import BacktestStatus, BacktestProvider
from models.user import User
from schemas.backtest import BacktestCreate


@pytest.mark.asyncio
class TestBacktestAPI:
    """Test backtest API endpoints."""
    
    @pytest.fixture
    def mock_user(self):
        """Create mock authenticated user."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.is_active = True
        return user
    
    @pytest.fixture
    def mock_strategy(self):
        """Create mock strategy."""
        strategy = Mock()
        strategy.id = 1
        strategy.name = "Test Strategy"
        strategy.created_by_id = 1
        return strategy
    
    @pytest.fixture
    def mock_backtest(self):
        """Create mock backtest."""
        backtest = Mock()
        backtest.id = 1
        backtest.name = "Test Backtest"
        backtest.strategy_id = 1
        backtest.created_by_id = 1
        backtest.status = BacktestStatus.QUEUED
        backtest.start_date = date(2023, 1, 1)
        backtest.end_date = date(2023, 12, 31)
        backtest.initial_capital = 10000
        backtest.provider = BacktestProvider.CUSTOM
        backtest.created_at = datetime.utcnow()
        backtest.updated_at = datetime.utcnow()
        return backtest
    
    @pytest.fixture
    def backtest_create_data(self):
        """Create backtest creation data."""
        return {
            "name": "Test Backtest",
            "description": "Test description",
            "strategy_id": 1,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 10000,
            "provider": "CUSTOM",
            "configuration": {"commission": 0.002}
        }
    
    @patch("api.backtests.BacktestingService")
    @patch("api.backtests.get_unit_of_work")
    @patch("api.backtests.get_current_active_user")
    async def test_create_backtest_success(
        self,
        mock_get_user,
        mock_get_uow,
        mock_service_class,
        test_client,
        mock_user,
        mock_strategy,
        backtest_create_data
    ):
        """Test successful backtest creation."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        
        mock_uow = AsyncMock()
        mock_uow.strategies.get.return_value = mock_strategy
        mock_uow.__aenter__.return_value = mock_uow
        mock_get_uow.return_value = mock_uow
        
        mock_service = AsyncMock()
        mock_service.create_and_run_backtest.return_value = {
            "backtest_id": 1,
            "status": "queued"
        }
        mock_service_class.return_value = mock_service
        
        # Make request
        response = await test_client.post(
            "/api/v1/backtests/",
            json=backtest_create_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Verify
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["backtest_id"] == 1
        assert data["status"] == "queued"
        
        # Verify service was called
        mock_service.create_and_run_backtest.assert_called_once()
    
    @patch("api.backtests.get_unit_of_work")
    @patch("api.backtests.get_current_active_user")
    async def test_create_backtest_strategy_not_found(
        self,
        mock_get_user,
        mock_get_uow,
        test_client,
        mock_user,
        backtest_create_data
    ):
        """Test creating backtest with non-existent strategy."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        
        mock_uow = AsyncMock()
        mock_uow.strategies.get.return_value = None
        mock_uow.__aenter__.return_value = mock_uow
        mock_get_uow.return_value = mock_uow
        
        # Make request
        response = await test_client.post(
            "/api/v1/backtests/",
            json=backtest_create_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Strategy not found" in response.json()["detail"]
    
    @patch("api.backtests.get_unit_of_work")
    @patch("api.backtests.get_current_active_user")
    async def test_create_backtest_unauthorized(
        self,
        mock_get_user,
        mock_get_uow,
        test_client,
        mock_user,
        mock_strategy,
        backtest_create_data
    ):
        """Test creating backtest for strategy not owned by user."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_strategy.created_by_id = 999  # Different user
        
        mock_uow = AsyncMock()
        mock_uow.strategies.get.return_value = mock_strategy
        mock_uow.__aenter__.return_value = mock_uow
        mock_get_uow.return_value = mock_uow
        
        # Make request
        response = await test_client.post(
            "/api/v1/backtests/",
            json=backtest_create_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Verify
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]
    
    @patch("api.backtests.get_db")
    @patch("api.backtests.get_backtest_repository")
    @patch("api.backtests.get_current_active_user")
    async def test_list_backtests(
        self,
        mock_get_user,
        mock_get_repo,
        mock_get_db,
        test_client,
        mock_user,
        mock_backtest
    ):
        """Test listing backtests."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_backtest]
        mock_db.execute.side_effect = [mock_result, Mock(scalar=Mock(return_value=1))]
        mock_get_db.return_value = mock_db
        
        mock_repo = AsyncMock()
        mock_get_repo.return_value = mock_repo
        
        # Make request
        response = await test_client.get(
            "/api/v1/backtests/",
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["backtests"]) == 1
        assert data["backtests"][0]["id"] == 1
    
    @patch("api.backtests.get_backtest_repository")
    @patch("api.backtests.get_current_active_user")
    async def test_get_backtest(
        self,
        mock_get_user,
        mock_get_repo,
        test_client,
        mock_user,
        mock_backtest
    ):
        """Test getting a specific backtest."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        
        mock_repo = AsyncMock()
        mock_repo.get.return_value = mock_backtest
        mock_get_repo.return_value = mock_repo
        
        # Make request
        response = await test_client.get(
            "/api/v1/backtests/1",
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Test Backtest"
    
    @patch("api.backtests.get_backtest_repository")
    @patch("api.backtests.get_current_active_user")
    async def test_get_backtest_not_found(
        self,
        mock_get_user,
        mock_get_repo,
        test_client,
        mock_user
    ):
        """Test getting non-existent backtest."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        
        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_repo.return_value = mock_repo
        
        # Make request
        response = await test_client.get(
            "/api/v1/backtests/999",
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Verify
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch("api.backtests.StrategyFactory")
    @patch("api.backtests.get_current_active_user")
    async def test_get_strategy_types(
        self,
        mock_get_user,
        mock_factory_class,
        test_client,
        mock_user
    ):
        """Test getting available strategy types."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        
        mock_factory = Mock()
        mock_factory.list_available_strategies.return_value = [
            "sma_crossover",
            "rsi_mean_reversion",
            "bollinger_bands",
            "momentum",
            "custom"
        ]
        mock_factory_class.return_value = mock_factory
        
        # Make request
        response = await test_client.get(
            "/api/v1/backtests/strategy-types",
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Verify
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert "sma_crossover" in data
        assert "rsi_mean_reversion" in data
        assert len(data) == 5