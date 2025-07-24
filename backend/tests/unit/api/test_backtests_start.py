"""Tests for backtest start endpoint with message publishing."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from uuid import uuid4

from src.models.user import User
from src.models.strategy import Strategy, StrategyType
from src.models.backtest import Backtest, BacktestStatus


@pytest.mark.asyncio
class TestBacktestStart:
    """Test backtest start endpoint functionality."""
    
    @pytest.fixture
    async def authenticated_client_with_backtest(self, async_client: AsyncClient, async_session: AsyncSession):
        """Create an authenticated client with a test user, strategy, and backtest."""
        # Register a test user
        user_data = {
            "name": "Backtest Test User",
            "email": "backteststart@example.com",
            "password": "testPassword123!",
            "role": "viewer"
        }
        
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        # Login to get access token
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Get the user from database
        from src.repositories.user import UserRepository
        user_repo = UserRepository(async_session)
        user = await user_repo.get_by_email(user_data["email"])
        
        # Create a test strategy
        from src.repositories.strategy import StrategyRepository
        strategy_repo = StrategyRepository(async_session)
        strategy = await strategy_repo.create(
            name="Test Strategy",
            description="Test strategy for backtest",
            type=StrategyType.MOMENTUM,
            code="def backtest(): return {'returns': 0.1}",
            created_by_id=user.id
        )
        
        # Create a test backtest
        from src.repositories.backtest import BacktestRepository
        backtest_repo = BacktestRepository(async_session)
        backtest = await backtest_repo.create(
            strategy_id=strategy.id,
            parameters={
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "initial_capital": 100000
            },
            created_by_id=user.id
        )
        
        yield async_client, user, strategy, backtest, headers
    
    async def test_start_backtest_success_with_message_publishing(self, authenticated_client_with_backtest):
        """Test successful backtest start with message publishing."""
        async_client, user, strategy, backtest, headers = authenticated_client_with_backtest
        
        # Mock message publisher
        with patch('src.api.backtests.MessagePublisher') as mock_publisher_class:
            mock_publisher = AsyncMock()
            message_id = uuid4()
            mock_publisher.publish_backtest_execution = AsyncMock(return_value=message_id)
            mock_publisher_class.return_value = mock_publisher
            
            # Start the backtest
            response = await async_client.post(
                f"/api/v1/backtests/{backtest.id}/start",
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify status was updated
            assert data["status"] == "running"
            assert data["started_at"] is not None
            
            # Verify message was published with correct parameters
            mock_publisher.publish_backtest_execution.assert_called_once_with(
                backtest_id=backtest.id,
                user_id=user.id,
                strategy_id=strategy.id,
                strategy_name=strategy.name,
                strategy_code=strategy.code,
                parameters=backtest.parameters
            )
    
    async def test_start_backtest_message_publisher_error_reverts_status(self, authenticated_client_with_backtest):
        """Test that backtest status is reverted if message publishing fails."""
        async_client, user, strategy, backtest, headers = authenticated_client_with_backtest
        
        # Mock message publisher to fail
        with patch('src.api.backtests.MessagePublisher') as mock_publisher_class:
            mock_publisher = AsyncMock()
            mock_publisher.publish_backtest_execution = AsyncMock(
                side_effect=Exception("RabbitMQ connection failed")
            )
            mock_publisher_class.return_value = mock_publisher
            
            # Mock logger to verify error logging
            with patch('src.api.backtests.logger') as mock_logger:
                # Try to start the backtest
                response = await async_client.post(
                    f"/api/v1/backtests/{backtest.id}/start",
                    headers=headers
                )
                
                # Should return 500 error
                assert response.status_code == 500
                assert response.json()["detail"] == "Failed to start backtest execution"
                
                # Verify error was logged
                mock_logger.error.assert_called_once()
                call_args = mock_logger.error.call_args
                assert call_args[0][0] == "Failed to publish backtest execution message"
                assert call_args[1]["backtest_id"] == backtest.id
                assert call_args[1]["strategy_id"] == strategy.id
                assert "RabbitMQ connection failed" in call_args[1]["error"]
                assert call_args[1]["exc_info"] is True
    
    async def test_start_backtest_already_running(self, authenticated_client_with_backtest, async_session: AsyncSession):
        """Test starting a backtest that's already running."""
        async_client, user, strategy, backtest, headers = authenticated_client_with_backtest
        
        # Update backtest status to running
        from src.repositories.backtest import BacktestRepository
        backtest_repo = BacktestRepository(async_session)
        await backtest_repo.update(backtest.id, status=BacktestStatus.RUNNING)
        
        # Try to start it again
        response = await async_client.post(
            f"/api/v1/backtests/{backtest.id}/start",
            headers=headers
        )
        
        assert response.status_code == 400
        assert "Cannot start backtest in running status" in response.json()["detail"]
    
    async def test_start_backtest_not_owner(self, authenticated_client_with_backtest, async_client: AsyncClient):
        """Test starting a backtest by non-owner."""
        _, _, _, backtest, _ = authenticated_client_with_backtest
        
        # Create another user
        other_user_data = {
            "name": "Other User",
            "email": "other@example.com",
            "password": "testPassword123!",
            "role": "viewer"
        }
        
        await async_client.post("/api/v1/auth/register", json=other_user_data)
        
        # Login as other user
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": other_user_data["email"],
            "password": other_user_data["password"]
        })
        
        other_tokens = login_response.json()
        other_headers = {"Authorization": f"Bearer {other_tokens['access_token']}"}
        
        # Try to start the backtest
        response = await async_client.post(
            f"/api/v1/backtests/{backtest.id}/start",
            headers=other_headers
        )
        
        assert response.status_code == 403
        assert "Not authorized to start this backtest" in response.json()["detail"]
    
    async def test_start_backtest_strategy_not_found(self, authenticated_client_with_backtest, async_session: AsyncSession):
        """Test starting a backtest when strategy is deleted."""
        async_client, user, strategy, backtest, headers = authenticated_client_with_backtest
        
        # Delete the strategy
        from src.repositories.strategy import StrategyRepository
        strategy_repo = StrategyRepository(async_session)
        await strategy_repo.delete(strategy.id)
        
        # Try to start the backtest
        response = await async_client.post(
            f"/api/v1/backtests/{backtest.id}/start",
            headers=headers
        )
        
        assert response.status_code == 404
        assert "Strategy not found" in response.json()["detail"]
    
    async def test_start_backtest_logging_includes_context(self, authenticated_client_with_backtest):
        """Test that successful message publishing includes proper logging context."""
        async_client, user, strategy, backtest, headers = authenticated_client_with_backtest
        
        # Mock message publisher
        with patch('src.api.backtests.MessagePublisher') as mock_publisher_class:
            mock_publisher = AsyncMock()
            message_id = uuid4()
            mock_publisher.publish_backtest_execution = AsyncMock(return_value=message_id)
            mock_publisher_class.return_value = mock_publisher
            
            # Mock logger
            with patch('src.api.backtests.logger') as mock_logger:
                # Start the backtest
                response = await async_client.post(
                    f"/api/v1/backtests/{backtest.id}/start",
                    headers=headers
                )
                
                assert response.status_code == 200
                
                # Verify info logging was called with proper context
                mock_logger.info.assert_called_once()
                call_args = mock_logger.info.call_args
                assert call_args[0][0] == "Published backtest execution message"
                assert call_args[1]["backtest_id"] == backtest.id
                assert call_args[1]["message_id"] == str(message_id)
                assert call_args[1]["strategy_id"] == strategy.id