"""Tests for strategy API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User, UserRole
from src.models.document import Document, DocumentStatus, DocumentType
from src.models.strategy import Strategy, StrategyStatus, AssetClass


@pytest.mark.asyncio
class TestStrategiesAPI:
    """Test strategy management API endpoints."""
    
    @pytest.fixture
    async def authenticated_client(self, async_client: AsyncClient, async_session: AsyncSession):
        """Create an authenticated client with a test user."""
        # Register a test user
        user_data = {
            "name": "Strategy Test User",
            "email": "strategytest@example.com",
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
        
        # Create a test document for strategies
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
        
        # Create headers with auth token
        headers = {"Authorization": f"Bearer {access_token}"}
        
        yield async_client, user, doc, headers
    
    async def test_create_strategy(self, authenticated_client):
        """Test creating a new strategy."""
        client, user, doc, headers = authenticated_client
        
        strategy_data = {
            "name": "Momentum Trading Strategy",
            "description": "A momentum-based trading strategy for equities",
            "asset_class": AssetClass.EQUITY.value,
            "source_document_id": doc.id,
            "parameters": {
                "lookback_period": 20,
                "threshold": 0.05
            },
            "entry_rules": {
                "condition": "price > moving_average",
                "confirmation": "volume > average_volume"
            },
            "exit_rules": {
                "stop_loss": 0.02,
                "take_profit": 0.05
            },
            "risk_parameters": {
                "max_position_size": 0.1,
                "max_portfolio_risk": 0.02
            }
        }
        
        response = await client.post(
            "/api/v1/strategies/",
            json=strategy_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == strategy_data["name"]
        assert data["description"] == strategy_data["description"]
        assert data["asset_class"] == strategy_data["asset_class"]
        assert data["status"] == StrategyStatus.DRAFT.value
        assert data["parameters"] == strategy_data["parameters"]
        assert data["entry_rules"] == strategy_data["entry_rules"]
        assert data["exit_rules"] == strategy_data["exit_rules"]
        assert data["risk_parameters"] == strategy_data["risk_parameters"]
        assert data["created_by_id"] == user.id
        assert data["source_document_id"] == doc.id
    
    async def test_create_strategy_unauthenticated(self, async_client: AsyncClient):
        """Test creating strategy without authentication."""
        strategy_data = {
            "name": "Test Strategy",
            "description": "Test description",
            "asset_class": AssetClass.EQUITY.value,
            "source_document_id": 1,
            "parameters": {},
            "entry_rules": {},
            "exit_rules": {},
            "risk_parameters": {}
        }
        
        response = await async_client.post("/api/v1/strategies/", json=strategy_data)
        
        assert response.status_code == 403  # HTTPBearer returns 403
    
    async def test_list_strategies(self, authenticated_client, async_session: AsyncSession):
        """Test listing user's strategies."""
        client, user, doc, headers = authenticated_client
        
        # Create test strategies
        strategies = []
        for i in range(3):
            strategy = Strategy(
                name=f"Strategy {i}",
                description=f"Description {i}",
                asset_class=AssetClass.EQUITY,
                status=StrategyStatus.ACTIVE,
                parameters={"param": i},
                entry_rules={"rule": f"entry_{i}"},
                exit_rules={"rule": f"exit_{i}"},
                risk_parameters={"risk": i},
                extraction_confidence=0.9,
                source_document_id=doc.id,
                created_by_id=user.id
            )
            async_session.add(strategy)
            strategies.append(strategy)
        
        await async_session.commit()
        
        response = await client.get("/api/v1/strategies/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["strategies"]) == 3
        assert data["skip"] == 0
        assert data["limit"] == 100
    
    async def test_list_strategies_with_filters(self, authenticated_client, async_session: AsyncSession):
        """Test listing strategies with status and asset class filters."""
        client, user, doc, headers = authenticated_client
        
        # Create strategies with different statuses and asset classes
        strategy1 = Strategy(
            name="Active Equity Strategy",
            description="Active equity strategy",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.ACTIVE,
            parameters={},
            entry_rules={},
            exit_rules={},
            risk_parameters={},
            extraction_confidence=0.9,
            source_document_id=doc.id,
            created_by_id=user.id
        )
        strategy2 = Strategy(
            name="Draft Crypto Strategy",
            description="Draft crypto strategy",
            asset_class=AssetClass.CRYPTO,
            status=StrategyStatus.DRAFT,
            parameters={},
            entry_rules={},
            exit_rules={},
            risk_parameters={},
            extraction_confidence=0.8,
            source_document_id=doc.id,
            created_by_id=user.id
        )
        
        async_session.add(strategy1)
        async_session.add(strategy2)
        await async_session.commit()
        
        # Filter by status
        response = await client.get(
            "/api/v1/strategies/",
            params={"status": StrategyStatus.ACTIVE.value},
            headers=headers
        )
        data = response.json()
        assert len(data["strategies"]) == 1
        assert data["strategies"][0]["status"] == StrategyStatus.ACTIVE.value
        
        # Filter by asset class
        response = await client.get(
            "/api/v1/strategies/",
            params={"asset_class": AssetClass.CRYPTO.value},
            headers=headers
        )
        data = response.json()
        assert len(data["strategies"]) == 1
        assert data["strategies"][0]["asset_class"] == AssetClass.CRYPTO.value
    
    async def test_list_strategies_pagination(self, authenticated_client, async_session: AsyncSession):
        """Test strategy list pagination."""
        client, user, doc, headers = authenticated_client
        
        # Create 5 strategies
        for i in range(5):
            strategy = Strategy(
                name=f"Strategy {i}",
                description=f"Description {i}",
                asset_class=AssetClass.EQUITY,
                status=StrategyStatus.ACTIVE,
                parameters={},
                entry_rules={},
                exit_rules={},
                risk_parameters={},
                extraction_confidence=0.9,
                source_document_id=doc.id,
                created_by_id=user.id
            )
            async_session.add(strategy)
        
        await async_session.commit()
        
        # Get first page
        response = await client.get("/api/v1/strategies/?skip=0&limit=2", headers=headers)
        data = response.json()
        assert len(data["strategies"]) == 2
        assert data["skip"] == 0
        assert data["limit"] == 2
        
        # Get second page
        response = await client.get("/api/v1/strategies/?skip=2&limit=2", headers=headers)
        data = response.json()
        assert len(data["strategies"]) == 2
        assert data["skip"] == 2
    
    async def test_get_strategy_by_id(self, authenticated_client, async_session: AsyncSession):
        """Test getting a specific strategy."""
        client, user, doc, headers = authenticated_client
        
        # Create a strategy
        strategy = Strategy(
            name="Test Strategy",
            description="Test strategy description",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.ACTIVE,
            parameters={"param": "value"},
            entry_rules={"rule": "entry"},
            exit_rules={"rule": "exit"},
            risk_parameters={"risk": "low"},
            extraction_confidence=0.95,
            expected_return=0.15,
            expected_volatility=0.20,
            sharpe_ratio=0.75,
            max_drawdown=0.10,
            source_document_id=doc.id,
            created_by_id=user.id
        )
        async_session.add(strategy)
        await async_session.commit()
        await async_session.refresh(strategy)
        
        response = await client.get(f"/api/v1/strategies/{strategy.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == strategy.id
        assert data["name"] == strategy.name
        assert data["asset_class"] == strategy.asset_class.value
        assert data["expected_return"] == strategy.expected_return
        assert data["sharpe_ratio"] == strategy.sharpe_ratio
    
    async def test_get_strategy_not_found(self, authenticated_client):
        """Test getting non-existent strategy."""
        client, user, doc, headers = authenticated_client
        
        response = await client.get("/api/v1/strategies/99999", headers=headers)
        
        assert response.status_code == 404
        assert "Strategy not found" in response.json()["detail"]
    
    async def test_get_strategy_not_owner(self, authenticated_client, async_session: AsyncSession):
        """Test getting strategy owned by another user."""
        client, user, doc, headers = authenticated_client
        
        # Create another user
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
        await async_session.refresh(other_user)
        
        # Create strategy owned by other user
        strategy = Strategy(
            name="Other's Strategy",
            description="Strategy owned by other user",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.ACTIVE,
            parameters={},
            entry_rules={},
            exit_rules={},
            risk_parameters={},
            extraction_confidence=0.9,
            source_document_id=doc.id,
            created_by_id=other_user.id
        )
        async_session.add(strategy)
        await async_session.commit()
        await async_session.refresh(strategy)
        
        response = await client.get(f"/api/v1/strategies/{strategy.id}", headers=headers)
        
        assert response.status_code == 403
        assert "Not authorized to access this strategy" in response.json()["detail"]
    
    async def test_update_strategy(self, authenticated_client, async_session: AsyncSession):
        """Test updating strategy details."""
        client, user, doc, headers = authenticated_client
        
        # Create a strategy
        strategy = Strategy(
            name="Original Strategy",
            description="Original description",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.DRAFT,
            parameters={"old": "value"},
            entry_rules={"old": "entry"},
            exit_rules={"old": "exit"},
            risk_parameters={"old": "risk"},
            extraction_confidence=0.8,
            source_document_id=doc.id,
            created_by_id=user.id
        )
        async_session.add(strategy)
        await async_session.commit()
        await async_session.refresh(strategy)
        
        # Update strategy
        update_data = {
            "name": "Updated Strategy",
            "description": "Updated description",
            "status": StrategyStatus.ACTIVE.value,
            "parameters": {"new": "value"},
            "entry_rules": {"new": "entry"},
            "exit_rules": {"new": "exit"},
            "risk_parameters": {"new": "risk"}
        }
        
        response = await client.patch(
            f"/api/v1/strategies/{strategy.id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["status"] == update_data["status"]
        assert data["parameters"] == update_data["parameters"]
        assert data["entry_rules"] == update_data["entry_rules"]
        assert data["exit_rules"] == update_data["exit_rules"]
        assert data["risk_parameters"] == update_data["risk_parameters"]
    
    async def test_update_strategy_not_owner(self, authenticated_client, async_session: AsyncSession):
        """Test updating strategy owned by another user."""
        client, user, doc, headers = authenticated_client
        
        # Create another user and their strategy
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
        
        strategy = Strategy(
            name="Other's Strategy",
            description="Strategy owned by other user",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.ACTIVE,
            parameters={},
            entry_rules={},
            exit_rules={},
            risk_parameters={},
            extraction_confidence=0.9,
            source_document_id=doc.id,
            created_by_id=other_user.id
        )
        async_session.add(strategy)
        await async_session.commit()
        await async_session.refresh(strategy)
        
        update_data = {"name": "Hacked Strategy"}
        
        response = await client.patch(
            f"/api/v1/strategies/{strategy.id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 403
        assert "Not authorized to update this strategy" in response.json()["detail"]
    
    async def test_delete_strategy(self, authenticated_client, async_session: AsyncSession):
        """Test deleting a strategy."""
        client, user, doc, headers = authenticated_client
        
        # Create a strategy
        strategy = Strategy(
            name="Strategy to Delete",
            description="This strategy will be deleted",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.DRAFT,
            parameters={},
            entry_rules={},
            exit_rules={},
            risk_parameters={},
            extraction_confidence=0.9,
            source_document_id=doc.id,
            created_by_id=user.id
        )
        async_session.add(strategy)
        await async_session.commit()
        await async_session.refresh(strategy)
        
        response = await client.delete(f"/api/v1/strategies/{strategy.id}", headers=headers)
        
        assert response.status_code == 204
        
        # Verify strategy was deleted
        response = await client.get(f"/api/v1/strategies/{strategy.id}", headers=headers)
        assert response.status_code == 404
    
    async def test_delete_strategy_not_owner(self, authenticated_client, async_session: AsyncSession):
        """Test deleting strategy owned by another user."""
        client, user, doc, headers = authenticated_client
        
        # Create another user and their strategy
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
        
        strategy = Strategy(
            name="Other's Strategy",
            description="Strategy owned by other user",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.ACTIVE,
            parameters={},
            entry_rules={},
            exit_rules={},
            risk_parameters={},
            extraction_confidence=0.9,
            source_document_id=doc.id,
            created_by_id=other_user.id
        )
        async_session.add(strategy)
        await async_session.commit()
        await async_session.refresh(strategy)
        
        response = await client.delete(f"/api/v1/strategies/{strategy.id}", headers=headers)
        
        assert response.status_code == 403
        assert "Not authorized to delete this strategy" in response.json()["detail"]
    
    async def test_get_strategies_by_document(self, authenticated_client, async_session: AsyncSession):
        """Test getting strategies from a specific document."""
        client, user, doc, headers = authenticated_client
        
        # Create strategies for the document
        strategies = []
        for i in range(3):
            strategy = Strategy(
                name=f"Doc Strategy {i}",
                description=f"Strategy {i} from document",
                asset_class=AssetClass.EQUITY,
                status=StrategyStatus.ACTIVE,
                parameters={},
                entry_rules={},
                exit_rules={},
                risk_parameters={},
                extraction_confidence=0.9,
                source_document_id=doc.id,
                created_by_id=user.id
            )
            async_session.add(strategy)
            strategies.append(strategy)
        
        # Create a strategy from another document
        other_doc = Document(
            filename="other.pdf",
            original_filename="other.pdf",
            document_type=DocumentType.STRATEGY_DOCUMENT,
            storage_path="/path/to/other.pdf",
            file_size=1000,
            mime_type="application/pdf",
            status=DocumentStatus.COMPLETED,
            uploaded_by_id=user.id
        )
        async_session.add(other_doc)
        await async_session.commit()
        await async_session.refresh(other_doc)
        
        other_strategy = Strategy(
            name="Other Doc Strategy",
            description="Strategy from other document",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.ACTIVE,
            parameters={},
            entry_rules={},
            exit_rules={},
            risk_parameters={},
            extraction_confidence=0.9,
            source_document_id=other_doc.id,
            created_by_id=user.id
        )
        async_session.add(other_strategy)
        await async_session.commit()
        
        response = await client.get(f"/api/v1/strategies/document/{doc.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(s["source_document_id"] == doc.id for s in data)
    
    async def test_activate_strategy(self, authenticated_client, async_session: AsyncSession):
        """Test activating a strategy."""
        client, user, doc, headers = authenticated_client
        
        # Create a draft strategy
        strategy = Strategy(
            name="Draft Strategy",
            description="Strategy to activate",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.DRAFT,
            parameters={},
            entry_rules={},
            exit_rules={},
            risk_parameters={},
            extraction_confidence=0.9,
            source_document_id=doc.id,
            created_by_id=user.id
        )
        async_session.add(strategy)
        await async_session.commit()
        await async_session.refresh(strategy)
        
        response = await client.post(f"/api/v1/strategies/{strategy.id}/activate", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == StrategyStatus.ACTIVE.value
    
    async def test_activate_strategy_not_owner(self, authenticated_client, async_session: AsyncSession):
        """Test activating strategy owned by another user."""
        client, user, doc, headers = authenticated_client
        
        # Create another user and their strategy
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
        
        strategy = Strategy(
            name="Other's Strategy",
            description="Strategy owned by other user",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.DRAFT,
            parameters={},
            entry_rules={},
            exit_rules={},
            risk_parameters={},
            extraction_confidence=0.9,
            source_document_id=doc.id,
            created_by_id=other_user.id
        )
        async_session.add(strategy)
        await async_session.commit()
        await async_session.refresh(strategy)
        
        response = await client.post(f"/api/v1/strategies/{strategy.id}/activate", headers=headers)
        
        assert response.status_code == 403
        assert "Not authorized to activate this strategy" in response.json()["detail"]
    
    async def test_deactivate_strategy(self, authenticated_client, async_session: AsyncSession):
        """Test deactivating a strategy."""
        client, user, doc, headers = authenticated_client
        
        # Create an active strategy
        strategy = Strategy(
            name="Active Strategy",
            description="Strategy to deactivate",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.ACTIVE,
            parameters={},
            entry_rules={},
            exit_rules={},
            risk_parameters={},
            extraction_confidence=0.9,
            source_document_id=doc.id,
            created_by_id=user.id
        )
        async_session.add(strategy)
        await async_session.commit()
        await async_session.refresh(strategy)
        
        response = await client.post(f"/api/v1/strategies/{strategy.id}/deactivate", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == StrategyStatus.PAUSED.value
    
    async def test_deactivate_strategy_not_owner(self, authenticated_client, async_session: AsyncSession):
        """Test deactivating strategy owned by another user."""
        client, user, doc, headers = authenticated_client
        
        # Create another user and their strategy
        other_user = User(
            email="other5@example.com",
            username="other5",
            full_name="Other User 5",
            hashed_password="hashed",
            role=UserRole.ANALYST,
            is_active=True,
            is_verified=True
        )
        async_session.add(other_user)
        await async_session.commit()
        
        strategy = Strategy(
            name="Other's Strategy",
            description="Strategy owned by other user",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.ACTIVE,
            parameters={},
            entry_rules={},
            exit_rules={},
            risk_parameters={},
            extraction_confidence=0.9,
            source_document_id=doc.id,
            created_by_id=other_user.id
        )
        async_session.add(strategy)
        await async_session.commit()
        await async_session.refresh(strategy)
        
        response = await client.post(f"/api/v1/strategies/{strategy.id}/deactivate", headers=headers)
        
        assert response.status_code == 403
        assert "Not authorized to deactivate this strategy" in response.json()["detail"]