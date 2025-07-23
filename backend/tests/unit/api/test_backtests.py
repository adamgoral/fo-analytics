"""Tests for backtest API endpoints."""

import pytest
from datetime import datetime, date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User, UserRole
from src.models.document import Document, DocumentStatus, DocumentType
from src.models.strategy import Strategy, StrategyStatus, AssetClass
from src.models.backtest import Backtest, BacktestStatus, BacktestProvider


@pytest.mark.asyncio
class TestBacktestsAPI:
    """Test backtest management API endpoints."""
    
    @pytest.fixture
    async def authenticated_client_with_strategy(self, async_client: AsyncClient, async_session: AsyncSession):
        """Create an authenticated client with a test user and strategy."""
        # Register a test user
        user_data = {
            "name": "Backtest Test User",
            "email": "backtestuser@example.com",
            "password": "testPassword123!",
            "role": "analyst"
        }
        
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        # Login to get access token
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        
        # Get the user from database for reference
        from src.repositories.user import UserRepository
        user_repo = UserRepository(async_session)
        user = await user_repo.get_by_email(user_data["email"])
        
        # Create a test document
        doc = Document(
            filename="strategies.pdf",
            original_filename="strategies.pdf",
            document_type=DocumentType.STRATEGY_DOCUMENT,
            storage_path="/path/to/strategies.pdf",
            file_size=1000,
            mime_type="application/pdf",
            status=DocumentStatus.COMPLETED,
            uploaded_by_id=user.id
        )
        async_session.add(doc)
        await async_session.commit()
        await async_session.refresh(doc)
        
        # Create a test strategy
        strategy = Strategy(
            name="Test Strategy",
            description="Strategy for backtest testing",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.ACTIVE,
            parameters={"param": "value"},
            entry_rules={"rule": "entry"},
            exit_rules={"rule": "exit"},
            risk_parameters={"risk": "low"},
            extraction_confidence=0.9,
            source_document_id=doc.id,
            created_by_id=user.id
        )
        async_session.add(strategy)
        await async_session.commit()
        await async_session.refresh(strategy)
        
        # Create headers with auth token
        headers = {"Authorization": f"Bearer {access_token}"}
        
        yield async_client, user, strategy, headers
    
    async def test_create_backtest(self, authenticated_client_with_strategy):
        """Test creating a new backtest."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        backtest_data = {
            "name": "Q1 2024 Backtest",
            "description": "Backtest for Q1 2024 performance",
            "strategy_id": strategy.id,
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "initial_capital": 100000.0,
            "provider": BacktestProvider.QUANTCONNECT.value,
            "configuration": {
                "commission": 0.001,
                "slippage": 0.0001,
                "data_frequency": "minute"
            }
        }
        
        response = await client.post(
            "/api/v1/backtests/",
            json=backtest_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == backtest_data["name"]
        assert data["description"] == backtest_data["description"]
        assert data["strategy_id"] == strategy.id
        assert data["start_date"] == backtest_data["start_date"]
        assert data["end_date"] == backtest_data["end_date"]
        assert data["initial_capital"] == backtest_data["initial_capital"]
        assert data["provider"] == backtest_data["provider"]
        assert data["configuration"] == backtest_data["configuration"]
        assert data["status"] == BacktestStatus.QUEUED.value
        assert data["created_by_id"] == user.id
    
    async def test_create_backtest_strategy_not_found(self, authenticated_client_with_strategy):
        """Test creating backtest for non-existent strategy."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        backtest_data = {
            "name": "Invalid Backtest",
            "description": "Test",
            "strategy_id": 99999,
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "initial_capital": 100000.0,
            "provider": BacktestProvider.QUANTCONNECT.value
        }
        
        response = await client.post("/api/v1/backtests/", json=backtest_data, headers=headers)
        
        assert response.status_code == 404
        assert "Strategy not found" in response.json()["detail"]
    
    async def test_create_backtest_not_strategy_owner(self, authenticated_client_with_strategy, async_session: AsyncSession):
        """Test creating backtest for strategy owned by another user."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        # Create another user and their strategy
        other_user = User(
            email="other@example.com",
            username="other",
            full_name="Other User",
            hashed_password="hashed",
            role=UserRole.ANALYST,
            is_active=True,
            is_verified=True
        )
        async_session.add(other_user)
        await async_session.commit()
        
        other_strategy = Strategy(
            name="Other's Strategy",
            description="Not accessible",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.ACTIVE,
            parameters={},
            entry_rules={},
            exit_rules={},
            risk_parameters={},
            extraction_confidence=0.9,
            source_document_id=strategy.source_document_id,
            created_by_id=other_user.id
        )
        async_session.add(other_strategy)
        await async_session.commit()
        await async_session.refresh(other_strategy)
        
        backtest_data = {
            "name": "Unauthorized Backtest",
            "description": "Should fail",
            "strategy_id": other_strategy.id,
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "initial_capital": 100000.0,
            "provider": BacktestProvider.QUANTCONNECT.value
        }
        
        response = await client.post("/api/v1/backtests/", json=backtest_data, headers=headers)
        
        assert response.status_code == 403
        assert "Not authorized to create backtests for this strategy" in response.json()["detail"]
    
    async def test_create_backtest_unauthenticated(self, async_client: AsyncClient):
        """Test creating backtest without authentication."""
        backtest_data = {
            "name": "Test Backtest",
            "description": "Test",
            "strategy_id": 1,
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "initial_capital": 100000.0,
            "provider": BacktestProvider.QUANTCONNECT.value
        }
        
        response = await async_client.post("/api/v1/backtests/", json=backtest_data)
        
        assert response.status_code == 403  # HTTPBearer returns 403
    
    async def test_list_backtests(self, authenticated_client_with_strategy, async_session: AsyncSession):
        """Test listing user's backtests."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        # Create test backtests
        backtests = []
        for i in range(3):
            backtest = Backtest(
                name=f"Backtest {i}",
                description=f"Description {i}",
                strategy_id=strategy.id,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 3, 31),
                initial_capital=100000.0,
                provider=BacktestProvider.QUANTCONNECT,
                status=BacktestStatus.COMPLETED,
                configuration={"test": i},
                total_return=0.1 * (i + 1),
                annualized_return=0.4 * (i + 1),
                volatility=0.15,
                sharpe_ratio=1.5,
                max_drawdown=0.05,
                win_rate=0.6,
                created_by_id=user.id
            )
            async_session.add(backtest)
            backtests.append(backtest)
        
        await async_session.commit()
        
        response = await client.get("/api/v1/backtests/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["backtests"]) == 3
        assert data["skip"] == 0
        assert data["limit"] == 100
    
    async def test_list_backtests_with_filters(self, authenticated_client_with_strategy, async_session: AsyncSession):
        """Test listing backtests with status and strategy filters."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        # Create backtests with different statuses
        backtest1 = Backtest(
            name="Running Backtest",
            description="Currently running",
            strategy_id=strategy.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            initial_capital=100000.0,
            provider=BacktestProvider.QUANTCONNECT,
            status=BacktestStatus.RUNNING,
            configuration={},
            created_by_id=user.id
        )
        backtest2 = Backtest(
            name="Completed Backtest",
            description="Finished",
            strategy_id=strategy.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            initial_capital=100000.0,
            provider=BacktestProvider.BACKTRADER,
            status=BacktestStatus.COMPLETED,
            configuration={},
            total_return=0.15,
            created_by_id=user.id
        )
        
        async_session.add(backtest1)
        async_session.add(backtest2)
        await async_session.commit()
        
        # Filter by status
        response = await client.get(
            "/api/v1/backtests/",
            params={"status": BacktestStatus.COMPLETED.value},
            headers=headers
        )
        data = response.json()
        assert data["total"] == 1
        assert data["backtests"][0]["status"] == BacktestStatus.COMPLETED.value
        
        # Filter by strategy
        response = await client.get(
            "/api/v1/backtests/",
            params={"strategy_id": strategy.id},
            headers=headers
        )
        data = response.json()
        assert data["total"] == 2
        assert all(b["strategy_id"] == strategy.id for b in data["backtests"])
    
    async def test_list_backtests_pagination(self, authenticated_client_with_strategy, async_session: AsyncSession):
        """Test backtest list pagination."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        # Create 5 backtests
        for i in range(5):
            backtest = Backtest(
                name=f"Backtest {i}",
                description=f"Description {i}",
                strategy_id=strategy.id,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 3, 31),
                initial_capital=100000.0,
                provider=BacktestProvider.QUANTCONNECT,
                status=BacktestStatus.COMPLETED,
                configuration={},
                created_by_id=user.id
            )
            async_session.add(backtest)
        
        await async_session.commit()
        
        # Get first page
        response = await client.get("/api/v1/backtests/?skip=0&limit=2", headers=headers)
        data = response.json()
        assert len(data["backtests"]) == 2
        assert data["skip"] == 0
        assert data["limit"] == 2
        
        # Get second page
        response = await client.get("/api/v1/backtests/?skip=2&limit=2", headers=headers)
        data = response.json()
        assert len(data["backtests"]) == 2
        assert data["skip"] == 2
    
    async def test_get_backtest_by_id(self, authenticated_client_with_strategy, async_session: AsyncSession):
        """Test getting a specific backtest."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        # Create a backtest
        backtest = Backtest(
            name="Test Backtest",
            description="Detailed backtest",
            strategy_id=strategy.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            initial_capital=100000.0,
            provider=BacktestProvider.QUANTCONNECT,
            status=BacktestStatus.COMPLETED,
            configuration={"commission": 0.001},
            total_return=0.25,
            annualized_return=1.0,
            volatility=0.18,
            sharpe_ratio=1.8,
            max_drawdown=0.08,
            win_rate=0.65,
            equity_curve={"dates": ["2024-01-01"], "values": [100000]},
            created_by_id=user.id
        )
        async_session.add(backtest)
        await async_session.commit()
        await async_session.refresh(backtest)
        
        response = await client.get(f"/api/v1/backtests/{backtest.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == backtest.id
        assert data["name"] == backtest.name
        assert data["total_return"] == backtest.total_return
        assert data["sharpe_ratio"] == backtest.sharpe_ratio
        assert data["equity_curve"] == backtest.equity_curve
    
    async def test_get_backtest_not_found(self, authenticated_client_with_strategy):
        """Test getting non-existent backtest."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        response = await client.get("/api/v1/backtests/99999", headers=headers)
        
        assert response.status_code == 404
        assert "Backtest not found" in response.json()["detail"]
    
    async def test_get_backtest_not_owner(self, authenticated_client_with_strategy, async_session: AsyncSession):
        """Test getting backtest owned by another user."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        # Create another user and their backtest
        other_user = User(
            email="other2@example.com",
            username="other2",
            full_name="Other User 2",
            hashed_password="hashed",
            role=UserRole.ANALYST,
            is_active=True,
            is_verified=True
        )
        async_session.add(other_user)
        await async_session.commit()
        
        other_backtest = Backtest(
            name="Other's Backtest",
            description="Not accessible",
            strategy_id=strategy.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            initial_capital=100000.0,
            provider=BacktestProvider.QUANTCONNECT,
            status=BacktestStatus.COMPLETED,
            configuration={},
            created_by_id=other_user.id
        )
        async_session.add(other_backtest)
        await async_session.commit()
        await async_session.refresh(other_backtest)
        
        response = await client.get(f"/api/v1/backtests/{other_backtest.id}", headers=headers)
        
        assert response.status_code == 403
        assert "Not authorized to access this backtest" in response.json()["detail"]
    
    async def test_update_backtest(self, authenticated_client_with_strategy, async_session: AsyncSession):
        """Test updating backtest details."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        # Create a backtest
        backtest = Backtest(
            name="Original Backtest",
            description="Original description",
            strategy_id=strategy.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            initial_capital=100000.0,
            provider=BacktestProvider.QUANTCONNECT,
            status=BacktestStatus.QUEUED,
            configuration={},
            created_by_id=user.id
        )
        async_session.add(backtest)
        await async_session.commit()
        await async_session.refresh(backtest)
        
        # Update backtest
        update_data = {
            "name": "Updated Backtest",
            "description": "Updated description",
            "status": BacktestStatus.RUNNING.value
        }
        
        response = await client.patch(
            f"/api/v1/backtests/{backtest.id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["status"] == update_data["status"]
    
    async def test_update_backtest_not_owner(self, authenticated_client_with_strategy, async_session: AsyncSession):
        """Test updating backtest owned by another user."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        # Create another user and their backtest
        other_user = User(
            email="other3@example.com",
            username="other3",
            full_name="Other User 3",
            hashed_password="hashed",
            role=UserRole.ANALYST,
            is_active=True,
            is_verified=True
        )
        async_session.add(other_user)
        await async_session.commit()
        
        other_backtest = Backtest(
            name="Other's Backtest",
            description="Not accessible",
            strategy_id=strategy.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            initial_capital=100000.0,
            provider=BacktestProvider.QUANTCONNECT,
            status=BacktestStatus.QUEUED,
            configuration={},
            created_by_id=other_user.id
        )
        async_session.add(other_backtest)
        await async_session.commit()
        await async_session.refresh(other_backtest)
        
        update_data = {"name": "Hacked Backtest"}
        
        response = await client.patch(
            f"/api/v1/backtests/{other_backtest.id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 403
        assert "Not authorized to update this backtest" in response.json()["detail"]
    
    async def test_delete_backtest(self, authenticated_client_with_strategy, async_session: AsyncSession):
        """Test deleting a backtest."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        # Create a backtest
        backtest = Backtest(
            name="Backtest to Delete",
            description="Will be deleted",
            strategy_id=strategy.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            initial_capital=100000.0,
            provider=BacktestProvider.QUANTCONNECT,
            status=BacktestStatus.COMPLETED,
            configuration={},
            created_by_id=user.id
        )
        async_session.add(backtest)
        await async_session.commit()
        await async_session.refresh(backtest)
        
        response = await client.delete(f"/api/v1/backtests/{backtest.id}", headers=headers)
        
        assert response.status_code == 204
        
        # Verify backtest was deleted
        response = await client.get(f"/api/v1/backtests/{backtest.id}", headers=headers)
        assert response.status_code == 404
    
    async def test_delete_backtest_not_owner(self, authenticated_client_with_strategy, async_session: AsyncSession):
        """Test deleting backtest owned by another user."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        # Create another user and their backtest
        other_user = User(
            email="other4@example.com",
            username="other4",
            full_name="Other User 4",
            hashed_password="hashed",
            role=UserRole.ANALYST,
            is_active=True,
            is_verified=True
        )
        async_session.add(other_user)
        await async_session.commit()
        
        other_backtest = Backtest(
            name="Other's Backtest",
            description="Not deletable",
            strategy_id=strategy.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            initial_capital=100000.0,
            provider=BacktestProvider.QUANTCONNECT,
            status=BacktestStatus.COMPLETED,
            configuration={},
            created_by_id=other_user.id
        )
        async_session.add(other_backtest)
        await async_session.commit()
        await async_session.refresh(other_backtest)
        
        response = await client.delete(f"/api/v1/backtests/{other_backtest.id}", headers=headers)
        
        assert response.status_code == 403
        assert "Not authorized to delete this backtest" in response.json()["detail"]
    
    async def test_get_backtests_by_strategy(self, authenticated_client_with_strategy, async_session: AsyncSession):
        """Test getting backtests for a specific strategy."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        # Create backtests for the strategy
        for i in range(3):
            backtest = Backtest(
                name=f"Strategy Backtest {i}",
                description=f"Backtest {i} for strategy",
                strategy_id=strategy.id,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 3, 31),
                initial_capital=100000.0,
                provider=BacktestProvider.QUANTCONNECT,
                status=BacktestStatus.COMPLETED,
                configuration={},
                created_by_id=user.id
            )
            async_session.add(backtest)
        
        await async_session.commit()
        
        response = await client.get(f"/api/v1/backtests/strategy/{strategy.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(b["strategy_id"] == strategy.id for b in data)
    
    async def test_start_backtest(self, authenticated_client_with_strategy, async_session: AsyncSession):
        """Test starting a queued backtest."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        # Create a queued backtest
        backtest = Backtest(
            name="Queued Backtest",
            description="Ready to start",
            strategy_id=strategy.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            initial_capital=100000.0,
            provider=BacktestProvider.QUANTCONNECT,
            status=BacktestStatus.QUEUED,
            configuration={},
            created_by_id=user.id
        )
        async_session.add(backtest)
        await async_session.commit()
        await async_session.refresh(backtest)
        
        response = await client.post(f"/api/v1/backtests/{backtest.id}/start", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == BacktestStatus.RUNNING.value
        assert data["started_at"] is not None
    
    async def test_start_backtest_invalid_status(self, authenticated_client_with_strategy, async_session: AsyncSession):
        """Test starting a backtest that's not queued."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        # Create a completed backtest
        backtest = Backtest(
            name="Completed Backtest",
            description="Already done",
            strategy_id=strategy.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            initial_capital=100000.0,
            provider=BacktestProvider.QUANTCONNECT,
            status=BacktestStatus.COMPLETED,
            configuration={},
            created_by_id=user.id
        )
        async_session.add(backtest)
        await async_session.commit()
        await async_session.refresh(backtest)
        
        response = await client.post(f"/api/v1/backtests/{backtest.id}/start", headers=headers)
        
        assert response.status_code == 400
        assert f"Cannot start backtest in {BacktestStatus.COMPLETED.value} status" in response.json()["detail"]
    
    async def test_cancel_backtest(self, authenticated_client_with_strategy, async_session: AsyncSession):
        """Test cancelling a running backtest."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        # Create a running backtest
        backtest = Backtest(
            name="Running Backtest",
            description="In progress",
            strategy_id=strategy.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            initial_capital=100000.0,
            provider=BacktestProvider.QUANTCONNECT,
            status=BacktestStatus.RUNNING,
            configuration={},
            started_at=datetime.utcnow(),
            created_by_id=user.id
        )
        async_session.add(backtest)
        await async_session.commit()
        await async_session.refresh(backtest)
        
        response = await client.post(f"/api/v1/backtests/{backtest.id}/cancel", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == BacktestStatus.CANCELLED.value
        assert data["completed_at"] is not None
    
    async def test_cancel_backtest_invalid_status(self, authenticated_client_with_strategy, async_session: AsyncSession):
        """Test cancelling a backtest that can't be cancelled."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        # Create a completed backtest
        backtest = Backtest(
            name="Completed Backtest",
            description="Already done",
            strategy_id=strategy.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            initial_capital=100000.0,
            provider=BacktestProvider.QUANTCONNECT,
            status=BacktestStatus.COMPLETED,
            configuration={},
            created_by_id=user.id
        )
        async_session.add(backtest)
        await async_session.commit()
        await async_session.refresh(backtest)
        
        response = await client.post(f"/api/v1/backtests/{backtest.id}/cancel", headers=headers)
        
        assert response.status_code == 400
        assert f"Cannot cancel backtest in {BacktestStatus.COMPLETED.value} status" in response.json()["detail"]
    
    async def test_upload_backtest_results(self, authenticated_client_with_strategy, async_session: AsyncSession):
        """Test uploading results for a running backtest."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        # Create a running backtest
        backtest = Backtest(
            name="Running Backtest",
            description="Processing",
            strategy_id=strategy.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            initial_capital=100000.0,
            provider=BacktestProvider.QUANTCONNECT,
            status=BacktestStatus.RUNNING,
            configuration={},
            started_at=datetime.utcnow(),
            created_by_id=user.id
        )
        async_session.add(backtest)
        await async_session.commit()
        await async_session.refresh(backtest)
        
        # Upload results
        results_data = {
            "total_return": 0.25,
            "annualized_return": 1.0,
            "volatility": 0.18,
            "sharpe_ratio": 1.8,
            "sortino_ratio": 2.1,
            "max_drawdown": 0.08,
            "win_rate": 0.65,
            "equity_curve": {
                "dates": ["2024-01-01", "2024-02-01", "2024-03-01"],
                "values": [100000, 110000, 125000]
            },
            "trades": {
                "count": 42,
                "winners": 27,
                "losers": 15
            },
            "statistics": {
                "avg_win": 0.05,
                "avg_loss": -0.02,
                "profit_factor": 2.5
            }
        }
        
        response = await client.post(
            f"/api/v1/backtests/{backtest.id}/results",
            json=results_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == BacktestStatus.COMPLETED.value
        assert data["total_return"] == results_data["total_return"]
        assert data["sharpe_ratio"] == results_data["sharpe_ratio"]
        assert data["equity_curve"] == results_data["equity_curve"]
        assert data["trades"] == results_data["trades"]
        assert data["statistics"] == results_data["statistics"]
        assert data["completed_at"] is not None
    
    async def test_upload_backtest_results_wrong_status(self, authenticated_client_with_strategy, async_session: AsyncSession):
        """Test uploading results for a backtest not in running status."""
        client, user, strategy, headers = authenticated_client_with_strategy
        
        # Create a queued backtest
        backtest = Backtest(
            name="Queued Backtest",
            description="Not started",
            strategy_id=strategy.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            initial_capital=100000.0,
            provider=BacktestProvider.QUANTCONNECT,
            status=BacktestStatus.QUEUED,
            configuration={},
            created_by_id=user.id
        )
        async_session.add(backtest)
        await async_session.commit()
        await async_session.refresh(backtest)
        
        results_data = {
            "total_return": 0.25,
            "annualized_return": 1.0,
            "volatility": 0.18,
            "sharpe_ratio": 1.8,
            "max_drawdown": 0.08,
            "win_rate": 0.65
        }
        
        response = await client.post(
            f"/api/v1/backtests/{backtest.id}/results",
            json=results_data,
            headers=headers
        )
        
        assert response.status_code == 400
        assert f"Cannot upload results for backtest in {BacktestStatus.QUEUED.value} status" in response.json()["detail"]