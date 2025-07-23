"""Tests for authentication service."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.auth_service import AuthService
from src.schemas.auth import UserCreate, UserLogin
from src.models.user import User, UserRole
from src.core.security import TokenData


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def auth_service(mock_db):
    """Create auth service with mocked dependencies."""
    return AuthService(mock_db)


@pytest.mark.asyncio
class TestAuthService:
    """Test authentication service methods."""
    
    async def test_register_success(self, auth_service):
        """Test successful user registration."""
        # Mock the repository methods
        auth_service.user_repo.get_by_email = AsyncMock(return_value=None)
        auth_service.user_repo.create = AsyncMock(return_value=User(
            id=1,
            email="newuser@example.com",
            username="newuser",
            full_name="New User",
            hashed_password="hashed",
            role=UserRole.VIEWER,
            is_active=True,
            is_verified=True
        ))
        
        user_data = UserCreate(
            name="New User",
            email="newuser@example.com",
            password="securePassword123!",
            role="viewer"
        )
        
        result = await auth_service.register(user_data)
        
        assert result.email == "newuser@example.com"
        assert result.full_name == "New User"
        auth_service.user_repo.get_by_email.assert_called_once_with("newuser@example.com")
        auth_service.user_repo.create.assert_called_once()
        
    async def test_register_existing_email(self, auth_service):
        """Test registration with already existing email."""
        # Mock finding existing user
        auth_service.user_repo.get_by_email = AsyncMock(return_value=User(
            id=1,
            email="existing@example.com",
            username="existing",
            full_name="Existing User",
            hashed_password="hashed",
            role=UserRole.VIEWER,
            is_active=True,
            is_verified=True
        ))
        
        user_data = UserCreate(
            name="New User",
            email="existing@example.com",
            password="securePassword123!",
            role="viewer"
        )
        
        with pytest.raises(ValueError, match="Email already registered"):
            await auth_service.register(user_data)
            
        auth_service.user_repo.get_by_email.assert_called_once_with("existing@example.com")
        
    async def test_login_success(self, auth_service):
        """Test successful login."""
        # Create a test user with known password
        test_password = "testPassword123!"
        hashed_password = "$2b$12$KIxQYzYBNFKfJz7Ks.r9luKqGp9kYl9VqGVqg5Qx5qCLJNgtdRBuS"  # pre-hashed for testing
        
        mock_user = User(
            id=1,
            email="logintest@example.com",
            username="logintest",
            full_name="Login Test",
            hashed_password=hashed_password,
            role=UserRole.VIEWER,
            is_active=True,
            is_verified=True
        )
        
        auth_service.user_repo.get_by_email = AsyncMock(return_value=mock_user)
        
        # Mock password verification
        with patch('src.services.auth_service.verify_password', return_value=True):
            login_data = UserLogin(
                email="logintest@example.com",
                password=test_password
            )
            
            user, tokens = await auth_service.login(login_data)
            
            assert user.email == "logintest@example.com"
            assert hasattr(tokens, 'access_token')
            assert hasattr(tokens, 'refresh_token')
            assert hasattr(tokens, 'token_type')
            assert tokens.access_token
            assert tokens.refresh_token
            assert tokens.token_type == "bearer"
            
    async def test_login_invalid_email(self, auth_service):
        """Test login with non-existent email."""
        auth_service.user_repo.get_by_email = AsyncMock(return_value=None)
        
        login_data = UserLogin(
            email="nonexistent@example.com",
            password="anyPassword123!"
        )
        
        with pytest.raises(ValueError, match="Invalid email or password"):
            await auth_service.login(login_data)
            
    async def test_login_wrong_password(self, auth_service):
        """Test login with wrong password."""
        mock_user = User(
            id=1,
            email="wrongpass@example.com",
            username="wrongpass",
            full_name="Wrong Pass",
            hashed_password="hashed_password",
            role=UserRole.VIEWER,
            is_active=True,
            is_verified=True
        )
        
        auth_service.user_repo.get_by_email = AsyncMock(return_value=mock_user)
        
        with patch('src.services.auth_service.verify_password', return_value=False):
            login_data = UserLogin(
                email="wrongpass@example.com",
                password="wrongPassword123!"
            )
            
            with pytest.raises(ValueError, match="Invalid email or password"):
                await auth_service.login(login_data)
                
    async def test_login_inactive_user(self, auth_service):
        """Test login with inactive user account."""
        mock_user = User(
            id=1,
            email="inactive@example.com",
            username="inactive",
            full_name="Inactive User",
            hashed_password="hashed_password",
            role=UserRole.VIEWER,
            is_active=False,
            is_verified=True
        )
        
        auth_service.user_repo.get_by_email = AsyncMock(return_value=mock_user)
        
        with patch('src.services.auth_service.verify_password', return_value=True):
            login_data = UserLogin(
                email="inactive@example.com",
                password="correctPassword123!"
            )
            
            with pytest.raises(ValueError, match="User account is inactive"):
                await auth_service.login(login_data)
                
    async def test_refresh_token_success(self, auth_service):
        """Test successful token refresh."""
        mock_user = User(
            id=1,
            email="refresh@example.com",
            username="refresh",
            full_name="Refresh User",
            hashed_password="hashed",
            role=UserRole.VIEWER,
            is_active=True,
            is_verified=True
        )
        
        auth_service.user_repo.get = AsyncMock(return_value=mock_user)
        
        # Mock token verification
        mock_token_payload = Mock()
        mock_token_payload.sub = "1"
        
        with patch('src.services.auth_service.verify_token', return_value=mock_token_payload):
            result = await auth_service.refresh_token("valid_refresh_token")
            
            assert hasattr(result, 'access_token')
            assert hasattr(result, 'refresh_token')
            assert hasattr(result, 'token_type')
            assert result.access_token
            assert result.refresh_token
            assert result.token_type == "bearer"
            
    async def test_refresh_token_invalid(self, auth_service):
        """Test refresh with invalid token."""
        with patch('src.services.auth_service.verify_token', return_value=None):
            result = await auth_service.refresh_token("invalid_token")
            assert result is None
            
    async def test_refresh_token_user_not_found(self, auth_service):
        """Test refresh token when user not found."""
        auth_service.user_repo.get = AsyncMock(return_value=None)
        
        mock_token_payload = Mock()
        mock_token_payload.sub = "999"
        
        with patch('src.services.auth_service.verify_token', return_value=mock_token_payload):
            result = await auth_service.refresh_token("valid_refresh_token")
            assert result is None
            
    async def test_change_password_success(self, auth_service):
        """Test successful password change."""
        mock_user = User(
            id=1,
            email="changepass@example.com",
            username="changepass",
            full_name="Change Pass",
            hashed_password="old_hashed_password",
            role=UserRole.VIEWER,
            is_active=True,
            is_verified=True
        )
        
        auth_service.user_repo.get = AsyncMock(return_value=mock_user)
        auth_service.user_repo.update = AsyncMock(return_value=mock_user)
        
        with patch('src.services.auth_service.verify_password', return_value=True):
            with patch('src.services.auth_service.get_password_hash', return_value="new_hashed_password"):
                result = await auth_service.change_password(
                    "1",
                    "oldPassword123!",
                    "newPassword123!"
                )
                
                assert result is True
                auth_service.user_repo.update.assert_called_once()
                
    async def test_change_password_wrong_current(self, auth_service):
        """Test password change with wrong current password."""
        mock_user = User(
            id=1,
            email="wrongcurrent@example.com",
            username="wrongcurrent",
            full_name="Wrong Current",
            hashed_password="hashed_password",
            role=UserRole.VIEWER,
            is_active=True,
            is_verified=True
        )
        
        auth_service.user_repo.get = AsyncMock(return_value=mock_user)
        
        with patch('src.services.auth_service.verify_password', return_value=False):
            result = await auth_service.change_password(
                "1",
                "wrongPassword123!",
                "newPassword123!"
            )
            
            assert result is False
            
    async def test_change_password_user_not_found(self, auth_service):
        """Test password change when user not found."""
        auth_service.user_repo.get = AsyncMock(return_value=None)
        
        result = await auth_service.change_password(
            "999",
            "anyPassword123!",
            "newPassword123!"
        )
        
        assert result is False