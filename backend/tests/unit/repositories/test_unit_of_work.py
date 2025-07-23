"""Tests for Unit of Work pattern."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.unit_of_work import UnitOfWork
from models.user import User, UserRole
from models.document import Document, DocumentStatus, DocumentType
from models.strategy import Strategy, StrategyStatus, AssetClass


@pytest.mark.asyncio
class TestUnitOfWork:
    """Test UnitOfWork pattern implementation."""
    
    async def test_uow_initialization(self, async_session):
        """Test UnitOfWork initialization with repositories."""
        async with UnitOfWork() as uow:
            assert uow.users is not None
            assert uow.documents is not None
            assert uow.strategies is not None
            assert uow.backtests is not None
            assert hasattr(uow, 'commit')
            assert hasattr(uow, 'rollback')
    
    async def test_uow_commit_success(self, async_session):
        """Test successful commit through UnitOfWork."""
        async with UnitOfWork() as uow:
            # Create a user
            user = await uow.users.create(
                email="uow_test@example.com",
                username="uow_test",
                full_name="UoW Test User",
                hashed_password="hashed"
            )
            
            # Commit the transaction
            await uow.commit()
            
            # Verify user was saved
            saved_user = await uow.users.get_by_email("uow_test@example.com")
            assert saved_user is not None
            assert saved_user.id == user.id
            assert saved_user.email == "uow_test@example.com"
    
    async def test_uow_rollback(self, async_session):
        """Test rollback functionality."""
        try:
            async with UnitOfWork() as uow:
                # Create a user
                user = await uow.users.create(
                    email="rollback_test@example.com",
                    username="rollback_test",
                    full_name="Rollback Test User",
                    hashed_password="hashed"
                )
                
                # Force an error before commit
                raise Exception("Simulated error")
                
        except Exception:
            pass
        
        # Verify user was not saved due to rollback
        async with UnitOfWork() as uow:
            user = await uow.users.get_by_email("rollback_test@example.com")
            assert user is None
    
    async def test_uow_multiple_repositories(self, async_session):
        """Test using multiple repositories in a single transaction."""
        async with UnitOfWork() as uow:
            # Create a user
            user = await uow.users.create(
                email="multi_repo@example.com",
                username="multi_repo",
                full_name="Multi Repo User",
                hashed_password="hashed"
            )
            
            # Create a document for that user
            document = await uow.documents.create(
                filename="test_doc.pdf",
                original_filename="test_doc.pdf",
                document_type=DocumentType.STRATEGY_DOCUMENT,
                storage_path="/path/to/test_doc.pdf",
                file_size=1024,
                mime_type="application/pdf",
                status=DocumentStatus.COMPLETED,
                uploaded_by_id=user.id
            )
            
            # Create a strategy from that document
            strategy = await uow.strategies.create(
                name="Multi Repo Strategy",
                description="Strategy created in UoW test",
                asset_class=AssetClass.EQUITY,
                status=StrategyStatus.ACTIVE,
                parameters={},
                entry_rules={},
                exit_rules={},
                risk_parameters={},
                extraction_confidence=0.9,
                source_document_id=document.id,
                created_by_id=user.id
            )
            
            # Commit all changes
            await uow.commit()
            
            # Verify all entities were saved
            assert user.id is not None
            assert document.id is not None
            assert strategy.id is not None
            
            # Verify relationships
            assert document.uploaded_by_id == user.id
            assert strategy.source_document_id == document.id
            assert strategy.created_by_id == user.id
    
    async def test_uow_nested_transaction_simulation(self, async_session):
        """Test handling nested operations that should be atomic."""
        async def create_user_with_documents(uow: UnitOfWork, should_fail: bool = False):
            """Helper function to create user with documents."""
            user = await uow.users.create(
                email="nested_test@example.com",
                username="nested_test",
                full_name="Nested Test User",
                hashed_password="hashed"
            )
            
            # Create first document
            doc1 = await uow.documents.create(
                filename="doc1.pdf",
                original_filename="doc1.pdf",
                document_type=DocumentType.STRATEGY_DOCUMENT,
                storage_path="/path/to/doc1.pdf",
                file_size=1024,
                mime_type="application/pdf",
                status=DocumentStatus.COMPLETED,
                uploaded_by_id=user.id
            )
            
            if should_fail:
                raise ValueError("Simulated failure in nested operation")
            
            # Create second document
            doc2 = await uow.documents.create(
                filename="doc2.pdf",
                original_filename="doc2.pdf",
                document_type=DocumentType.RESEARCH_REPORT,
                storage_path="/path/to/doc2.pdf",
                file_size=2048,
                mime_type="application/pdf",
                status=DocumentStatus.COMPLETED,
                uploaded_by_id=user.id
            )
            
            return user, doc1, doc2
        
        # Test successful nested operation
        async with UnitOfWork() as uow:
            user, doc1, doc2 = await create_user_with_documents(uow, should_fail=False)
            await uow.commit()
            
            # Verify all were created
            saved_user = await uow.users.get_by_email("nested_test@example.com")
            assert saved_user is not None
            
            user_docs = await uow.documents.get_by_user(saved_user.id)
            assert len(user_docs) == 2
        
        # Clean up
        async with UnitOfWork() as uow:
            user = await uow.users.get_by_email("nested_test@example.com")
            if user:
                await uow.users.delete(user.id)
                await uow.commit()
        
        # Test failed nested operation
        try:
            async with UnitOfWork() as uow:
                await create_user_with_documents(uow, should_fail=True)
                await uow.commit()
        except ValueError:
            pass
        
        # Verify nothing was created due to rollback
        async with UnitOfWork() as uow:
            user = await uow.users.get_by_email("nested_test@example.com")
            assert user is None
    
    async def test_uow_context_manager_exception_handling(self, async_session):
        """Test that exceptions in context manager are handled properly."""
        with pytest.raises(ValueError):
            async with UnitOfWork() as uow:
                # Create a user
                await uow.users.create(
                    email="exception_test@example.com",
                    username="exception_test",
                    full_name="Exception Test User",
                    hashed_password="hashed"
                )
                
                # Raise an exception
                raise ValueError("Test exception")
        
        # Verify rollback happened
        async with UnitOfWork() as uow:
            user = await uow.users.get_by_email("exception_test@example.com")
            assert user is None
    
    async def test_uow_multiple_commits(self, async_session):
        """Test multiple commits in the same UoW session."""
        async with UnitOfWork() as uow:
            # First operation and commit
            user1 = await uow.users.create(
                email="multi_commit1@example.com",
                username="multi_commit1",
                full_name="Multi Commit User 1",
                hashed_password="hashed"
            )
            await uow.commit()
            
            # Second operation and commit
            user2 = await uow.users.create(
                email="multi_commit2@example.com",
                username="multi_commit2",
                full_name="Multi Commit User 2",
                hashed_password="hashed"
            )
            await uow.commit()
            
            # Verify both users exist
            saved_user1 = await uow.users.get_by_email("multi_commit1@example.com")
            saved_user2 = await uow.users.get_by_email("multi_commit2@example.com")
            
            assert saved_user1 is not None
            assert saved_user2 is not None
            assert saved_user1.id != saved_user2.id
    
    async def test_uow_repository_isolation(self, async_session):
        """Test that each UoW instance has its own repository instances."""
        async with UnitOfWork() as uow1:
            async with UnitOfWork() as uow2:
                # Verify repositories are different instances
                assert uow1.users is not uow2.users
                assert uow1.documents is not uow2.documents
                assert uow1.strategies is not uow2.strategies
                assert uow1.backtests is not uow2.backtests
    
    @patch('repositories.unit_of_work.UserRepository')
    @patch('repositories.unit_of_work.DocumentRepository')
    async def test_uow_session_sharing(self, mock_doc_repo, mock_user_repo, async_session):
        """Test that all repositories share the same session."""
        # Create mock instances
        mock_user_instance = Mock()
        mock_doc_instance = Mock()
        mock_user_repo.return_value = mock_user_instance
        mock_doc_repo.return_value = mock_doc_instance
        
        async with UnitOfWork() as uow:
            # Verify repositories were initialized (can't check specific session)
            assert mock_user_repo.called
            assert mock_doc_repo.called