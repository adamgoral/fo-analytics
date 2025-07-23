"""Tests for user service layer."""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from uuid import UUID

from services.user_service import UserService, UserServiceWithUoW
from models.user import User, UserRole
from repositories.user import UserRepository
from repositories.unit_of_work import UnitOfWork


@pytest.mark.asyncio
class TestUserService:
    """Test UserService business logic."""
    
    @pytest.fixture
    def mock_user_repository(self):
        """Create a mock user repository."""
        repo = Mock(spec=UserRepository)
        repo.get = AsyncMock()
        repo.get_by_email = AsyncMock()
        repo.get_by_username = AsyncMock()
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.delete = AsyncMock()
        return repo
    
    @pytest.fixture
    def user_service(self, mock_user_repository):
        """Create user service with mock repository."""
        return UserService(mock_user_repository)
    
    @pytest.fixture
    def sample_user(self):
        """Create a sample user."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.username = "testuser"
        user.full_name = "Test User"
        user.is_active = True
        user.is_verified = True
        user.role = UserRole.ANALYST
        user.created_at = datetime(2024, 1, 1, 12, 0, 0)
        user.updated_at = datetime(2024, 1, 1, 12, 0, 0)
        return user
    
    async def test_get_user_by_id_success(self, user_service, mock_user_repository, sample_user):
        """Test successfully getting a user by ID."""
        mock_user_repository.get.return_value = sample_user
        
        result = await user_service.get_user_by_id(UUID("00000000-0000-0000-0000-000000000001"))
        
        assert result is not None
        assert result["id"] == "1"
        assert result["email"] == "test@example.com"
        assert result["username"] == "testuser"
        assert result["full_name"] == "Test User"
        assert result["is_active"] is True
        assert result["created_at"] == "2024-01-01T12:00:00"
        
        mock_user_repository.get.assert_called_once()
    
    async def test_get_user_by_id_not_found(self, user_service, mock_user_repository):
        """Test getting non-existent user by ID."""
        mock_user_repository.get.return_value = None
        
        result = await user_service.get_user_by_id(UUID("00000000-0000-0000-0000-000000000999"))
        
        assert result is None
        mock_user_repository.get.assert_called_once()
    
    async def test_create_user_success(self, user_service, mock_user_repository, sample_user):
        """Test successfully creating a new user."""
        mock_user_repository.get_by_email.return_value = None
        mock_user_repository.get_by_username.return_value = None
        mock_user_repository.create.return_value = sample_user
        
        result = await user_service.create_user(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password="hashed_password_123"
        )
        
        assert result["id"] == "1"
        assert result["email"] == "test@example.com"
        assert result["username"] == "testuser"
        assert result["full_name"] == "Test User"
        assert result["is_active"] is True
        assert result["created_at"] == "2024-01-01T12:00:00"
        
        mock_user_repository.get_by_email.assert_called_once_with("test@example.com")
        mock_user_repository.get_by_username.assert_called_once_with("testuser")
        mock_user_repository.create.assert_called_once_with(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password="hashed_password_123"
        )
    
    async def test_create_user_email_already_exists(self, user_service, mock_user_repository, sample_user):
        """Test creating user with existing email."""
        mock_user_repository.get_by_email.return_value = sample_user
        
        with pytest.raises(ValueError, match="User with this email already exists"):
            await user_service.create_user(
                email="test@example.com",
                username="newuser",
                full_name="New User",
                hashed_password="hashed_password"
            )
        
        mock_user_repository.get_by_email.assert_called_once_with("test@example.com")
        mock_user_repository.get_by_username.assert_not_called()
        mock_user_repository.create.assert_not_called()
    
    async def test_create_user_username_already_exists(self, user_service, mock_user_repository, sample_user):
        """Test creating user with existing username."""
        mock_user_repository.get_by_email.return_value = None
        mock_user_repository.get_by_username.return_value = sample_user
        
        with pytest.raises(ValueError, match="User with this username already exists"):
            await user_service.create_user(
                email="new@example.com",
                username="testuser",
                full_name="New User",
                hashed_password="hashed_password"
            )
        
        mock_user_repository.get_by_email.assert_called_once_with("new@example.com")
        mock_user_repository.get_by_username.assert_called_once_with("testuser")
        mock_user_repository.create.assert_not_called()


@pytest.mark.asyncio
class TestUserServiceWithUoW:
    """Test UserServiceWithUoW business logic."""
    
    @pytest.fixture
    def mock_uow(self):
        """Create a mock unit of work."""
        uow = Mock(spec=UnitOfWork)
        uow.users = Mock()
        uow.documents = Mock()
        uow.commit = AsyncMock()
        uow.rollback = AsyncMock()
        
        # Mock user repository methods
        uow.users.create = AsyncMock()
        uow.users.get = AsyncMock()
        
        # Mock document repository methods
        uow.documents.create = AsyncMock()
        
        return uow
    
    @pytest.fixture
    def user_service_uow(self, mock_uow):
        """Create user service with unit of work."""
        return UserServiceWithUoW(mock_uow)
    
    @pytest.fixture
    def sample_user(self):
        """Create a sample user."""
        user = Mock()
        user.id = 1
        user.email = "test@example.com"
        user.username = "testuser"
        user.full_name = "Test User"
        user.is_active = True
        return user
    
    @pytest.fixture
    def sample_document(self):
        """Create a sample document."""
        doc = Mock()
        doc.id = 1
        doc.name = "test_document.txt"
        doc.status = "pending"
        doc.user_id = 1
        return doc
    
    async def test_create_user_with_initial_document_success(
        self, user_service_uow, mock_uow, sample_user, sample_document
    ):
        """Test successfully creating user with initial document."""
        mock_uow.users.create.return_value = sample_user
        mock_uow.documents.create.return_value = sample_document
        
        result = await user_service_uow.create_user_with_initial_document(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password="hashed_password",
            document_name="test_document.txt",
            document_content="Test content"
        )
        
        assert result["user"]["id"] == "1"
        assert result["user"]["email"] == "test@example.com"
        assert result["user"]["username"] == "testuser"
        assert result["document"]["id"] == "1"
        assert result["document"]["name"] == "test_document.txt"
        assert result["document"]["status"] == "pending"
        
        mock_uow.users.create.assert_called_once_with(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password="hashed_password"
        )
        
        mock_uow.documents.create.assert_called_once_with(
            user_id=1,
            name="test_document.txt",
            content="Test content",
            file_type="text",
            status="pending"
        )
        
        mock_uow.commit.assert_called_once()
        mock_uow.rollback.assert_not_called()
    
    async def test_create_user_with_initial_document_user_creation_fails(
        self, user_service_uow, mock_uow
    ):
        """Test handling user creation failure."""
        mock_uow.users.create.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            await user_service_uow.create_user_with_initial_document(
                email="test@example.com",
                username="testuser",
                full_name="Test User",
                hashed_password="hashed_password",
                document_name="test_document.txt",
                document_content="Test content"
            )
        
        mock_uow.users.create.assert_called_once()
        mock_uow.documents.create.assert_not_called()
        mock_uow.commit.assert_not_called()
        mock_uow.rollback.assert_called_once()
    
    async def test_create_user_with_initial_document_document_creation_fails(
        self, user_service_uow, mock_uow, sample_user
    ):
        """Test handling document creation failure."""
        mock_uow.users.create.return_value = sample_user
        mock_uow.documents.create.side_effect = Exception("Document error")
        
        with pytest.raises(Exception, match="Document error"):
            await user_service_uow.create_user_with_initial_document(
                email="test@example.com",
                username="testuser",
                full_name="Test User",
                hashed_password="hashed_password",
                document_name="test_document.txt",
                document_content="Test content"
            )
        
        mock_uow.users.create.assert_called_once()
        mock_uow.documents.create.assert_called_once()
        mock_uow.commit.assert_not_called()
        mock_uow.rollback.assert_called_once()
    
    async def test_create_user_with_initial_document_commit_fails(
        self, user_service_uow, mock_uow, sample_user, sample_document
    ):
        """Test handling commit failure."""
        mock_uow.users.create.return_value = sample_user
        mock_uow.documents.create.return_value = sample_document
        mock_uow.commit.side_effect = Exception("Commit failed")
        
        with pytest.raises(Exception, match="Commit failed"):
            await user_service_uow.create_user_with_initial_document(
                email="test@example.com",
                username="testuser",
                full_name="Test User",
                hashed_password="hashed_password",
                document_name="test_document.txt",
                document_content="Test content"
            )
        
        mock_uow.users.create.assert_called_once()
        mock_uow.documents.create.assert_called_once()
        mock_uow.commit.assert_called_once()
        mock_uow.rollback.assert_called_once()