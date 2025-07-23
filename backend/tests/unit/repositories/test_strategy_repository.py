"""Tests for strategy repository."""

import pytest
from datetime import datetime

from models.strategy import Strategy, StrategyStatus, AssetClass
from models.document import Document, DocumentStatus, DocumentType
from models.user import User, UserRole
from repositories.strategy import StrategyRepository


@pytest.mark.asyncio
class TestStrategyRepository:
    """Test StrategyRepository database operations."""
    
    @pytest.fixture
    async def test_user(self, async_session):
        """Create a test user."""
        user = User(
            email="strattest@example.com",
            username="strattest",
            full_name="Strategy Test User",
            hashed_password="hashed",
            role=UserRole.ANALYST,
            is_active=True,
            is_verified=True
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)
        return user
    
    @pytest.fixture
    async def test_document(self, async_session, test_user):
        """Create a test document."""
        doc = Document(
            filename="strategies.pdf",
            original_filename="strategies.pdf",
            document_type=DocumentType.STRATEGY_DOCUMENT,
            storage_path="/path/to/strategies.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status=DocumentStatus.COMPLETED,
            uploaded_by_id=test_user.id
        )
        async_session.add(doc)
        await async_session.commit()
        await async_session.refresh(doc)
        return doc
    
    @pytest.fixture
    def strategy_repo(self, async_session):
        """Create strategy repository instance."""
        return StrategyRepository(async_session)
    
    async def test_create_strategy(self, strategy_repo, test_user, test_document):
        """Test creating a strategy."""
        strategy = await strategy_repo.create(
            name="Test Strategy",
            description="A test trading strategy",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.DRAFT,
            parameters={"param1": "value1", "param2": 100},
            entry_rules={"rule": "buy when MA crosses"},
            exit_rules={"rule": "sell when profit > 10%"},
            risk_parameters={"max_loss": 0.02, "position_size": 0.1},
            extraction_confidence=0.95,
            source_document_id=test_document.id,
            created_by_id=test_user.id
        )
        
        assert strategy.id is not None
        assert strategy.name == "Test Strategy"
        assert strategy.description == "A test trading strategy"
        assert strategy.asset_class == AssetClass.EQUITY
        assert strategy.status == StrategyStatus.DRAFT
        assert strategy.parameters == {"param1": "value1", "param2": 100}
        assert strategy.entry_rules == {"rule": "buy when MA crosses"}
        assert strategy.exit_rules == {"rule": "sell when profit > 10%"}
        assert strategy.risk_parameters == {"max_loss": 0.02, "position_size": 0.1}
        assert strategy.extraction_confidence == 0.95
        assert strategy.source_document_id == test_document.id
        assert strategy.created_by_id == test_user.id
    
    async def test_get_by_user(self, strategy_repo, test_user, test_document, async_session):
        """Test getting strategies by user."""
        # Create multiple strategies
        for i in range(3):
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
                source_document_id=test_document.id,
                created_by_id=test_user.id
            )
            async_session.add(strategy)
        
        # Create strategy for another user
        other_user = User(
            email="other_strat@example.com",
            username="other_strat",
            full_name="Other User",
            hashed_password="hashed",
            role=UserRole.VIEWER,
            is_active=True,
            is_verified=True
        )
        async_session.add(other_user)
        await async_session.commit()
        
        other_strategy = Strategy(
            name="Other's Strategy",
            description="Not visible",
            asset_class=AssetClass.FIXED_INCOME,
            status=StrategyStatus.ACTIVE,
            parameters={},
            entry_rules={},
            exit_rules={},
            risk_parameters={},
            extraction_confidence=0.8,
            source_document_id=test_document.id,
            created_by_id=other_user.id
        )
        async_session.add(other_strategy)
        await async_session.commit()
        
        # Get strategies for test user
        user_strategies = await strategy_repo.get_by_user(test_user.id)
        
        assert len(user_strategies) == 3
        assert all(s.created_by_id == test_user.id for s in user_strategies)
        assert all(s.name.startswith("Strategy") for s in user_strategies)
    
    async def test_get_by_status(self, strategy_repo, test_user, test_document, async_session):
        """Test getting strategies by status."""
        # Create strategies with different statuses
        statuses = [
            StrategyStatus.DRAFT,
            StrategyStatus.ACTIVE,
            StrategyStatus.INACTIVE,
            StrategyStatus.ARCHIVED
        ]
        
        for i, status in enumerate(statuses):
            strategy = Strategy(
                name=f"Status Strategy {i}",
                description=f"Strategy with status {status}",
                asset_class=AssetClass.EQUITY,
                status=status,
                parameters={},
                entry_rules={},
                exit_rules={},
                risk_parameters={},
                extraction_confidence=0.9,
                source_document_id=test_document.id,
                created_by_id=test_user.id
            )
            async_session.add(strategy)
        await async_session.commit()
        
        # Get active strategies
        active_strategies = await strategy_repo.get_by_status(StrategyStatus.ACTIVE.value)
        assert len(active_strategies) == 1
        assert active_strategies[0].status == StrategyStatus.ACTIVE
        
        # Get draft strategies
        draft_strategies = await strategy_repo.get_by_status(StrategyStatus.DRAFT.value)
        assert len(draft_strategies) == 1
        assert draft_strategies[0].status == StrategyStatus.DRAFT
    
    async def test_get_recent_strategies(self, strategy_repo, test_user, test_document, async_session):
        """Test getting recent strategies."""
        # Create strategies
        for i in range(5):
            strategy = Strategy(
                name=f"Recent Strategy {i}",
                description=f"Strategy {i}",
                asset_class=AssetClass.EQUITY,
                status=StrategyStatus.ACTIVE,
                parameters={},
                entry_rules={},
                exit_rules={},
                risk_parameters={},
                extraction_confidence=0.9,
                source_document_id=test_document.id,
                created_by_id=test_user.id
            )
            async_session.add(strategy)
        await async_session.commit()
        
        # Get recent strategies
        recent_strategies = await strategy_repo.get_recent(limit=3)
        
        assert len(recent_strategies) <= 3
        # Verify they are ordered by creation date (most recent first)
        if len(recent_strategies) > 1:
            for i in range(len(recent_strategies) - 1):
                assert recent_strategies[i].created_at >= recent_strategies[i+1].created_at
    
    async def test_get_by_document(self, strategy_repo, test_user, test_document, async_session):
        """Test getting strategies by source document."""
        # Create another document
        other_doc = Document(
            filename="other_strategies.pdf",
            original_filename="other_strategies.pdf",
            document_type=DocumentType.STRATEGY_DOCUMENT,
            storage_path="/path/to/other_strategies.pdf",
            file_size=2048,
            mime_type="application/pdf",
            status=DocumentStatus.COMPLETED,
            uploaded_by_id=test_user.id
        )
        async_session.add(other_doc)
        await async_session.commit()
        
        # Create strategies for test document
        for i in range(2):
            strategy = Strategy(
                name=f"Doc Strategy {i}",
                description=f"From test document",
                asset_class=AssetClass.EQUITY,
                status=StrategyStatus.ACTIVE,
                parameters={},
                entry_rules={},
                exit_rules={},
                risk_parameters={},
                extraction_confidence=0.9,
                source_document_id=test_document.id,
                created_by_id=test_user.id
            )
            async_session.add(strategy)
        
        # Create strategy for other document
        other_strategy = Strategy(
            name="Other Doc Strategy",
            description="From other document",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.ACTIVE,
            parameters={},
            entry_rules={},
            exit_rules={},
            risk_parameters={},
            extraction_confidence=0.85,
            source_document_id=other_doc.id,
            created_by_id=test_user.id
        )
        async_session.add(other_strategy)
        await async_session.commit()
        
        # Get strategies from test document
        doc_strategies = await strategy_repo.get_by_document(test_document.id)
        
        assert len(doc_strategies) == 2
        assert all(s.source_document_id == test_document.id for s in doc_strategies)
        assert all(s.name.startswith("Doc Strategy") for s in doc_strategies)
    
    async def test_update_strategy(self, strategy_repo, test_user, test_document):
        """Test updating a strategy."""
        # Create a strategy
        strategy = await strategy_repo.create(
            name="Update Test Strategy",
            description="Original description",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.DRAFT,
            parameters={},
            entry_rules={},
            exit_rules={},
            risk_parameters={},
            extraction_confidence=0.8,
            source_document_id=test_document.id,
            created_by_id=test_user.id
        )
        
        # Update strategy
        updated = await strategy_repo.update(
            strategy.id,
            name="Updated Strategy Name",
            description="Updated description",
            status=StrategyStatus.ACTIVE,
            parameters={"new_param": "value"},
            performance_metrics={"sharpe_ratio": 1.5, "total_return": 0.25}
        )
        
        assert updated.name == "Updated Strategy Name"
        assert updated.description == "Updated description"
        assert updated.status == StrategyStatus.ACTIVE
        assert updated.parameters == {"new_param": "value"}
        assert updated.performance_metrics == {"sharpe_ratio": 1.5, "total_return": 0.25}
        assert updated.asset_class == AssetClass.EQUITY  # Unchanged
    
    async def test_delete_strategy(self, strategy_repo, test_user, test_document):
        """Test deleting a strategy."""
        # Create a strategy
        strategy = await strategy_repo.create(
            name="Delete Test Strategy",
            description="To be deleted",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.DRAFT,
            parameters={},
            entry_rules={},
            exit_rules={},
            risk_parameters={},
            extraction_confidence=0.7,
            source_document_id=test_document.id,
            created_by_id=test_user.id
        )
        
        # Delete strategy
        await strategy_repo.delete(strategy.id)
        
        # Try to get deleted strategy
        deleted = await strategy_repo.get(strategy.id)
        assert deleted is None
    
    async def test_update_status(self, strategy_repo, test_user, test_document):
        """Test updating strategy status."""
        # Create a strategy
        strategy = await strategy_repo.create(
            name="Status Update Strategy",
            description="Test status updates",
            asset_class=AssetClass.EQUITY,
            status=StrategyStatus.DRAFT,
            parameters={},
            entry_rules={},
            exit_rules={},
            risk_parameters={},
            extraction_confidence=0.9,
            source_document_id=test_document.id,
            created_by_id=test_user.id
        )
        
        # Update status
        updated = await strategy_repo.update_status(strategy.id, StrategyStatus.ACTIVE.value)
        
        assert updated is not None
        assert updated.status == StrategyStatus.ACTIVE.value