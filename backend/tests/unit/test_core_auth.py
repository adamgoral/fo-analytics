"""Tests for core authentication module."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from src.core.auth import (
    get_current_user,
    get_current_active_user,
    require_role,
    get_admin_user,
    get_analyst_user
)
from src.models.user import User, UserRole


@pytest.mark.asyncio
class TestCoreAuth:
    """Test core authentication functions."""
    
    async def test_get_current_user_success(self):
        """Test getting current user with valid token."""
        # Mock dependencies
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid_token"
        
        mock_db = AsyncMock()
        
        mock_user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password="hashed",
            role=UserRole.VIEWER,
            is_active=True,
            is_verified=True
        )
        
        # Mock token verification and user repo
        mock_token_payload = Mock()
        mock_token_payload.sub = "1"
        
        with patch('src.core.auth.verify_token', return_value=mock_token_payload):
            with patch('src.core.auth.UserRepository') as mock_repo_class:
                mock_repo = mock_repo_class.return_value
                mock_repo.get = AsyncMock(return_value=mock_user)
                
                result = await get_current_user(mock_credentials, mock_db)
                
                assert result == mock_user
                mock_repo.get.assert_called_once_with("1")
                
    async def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid_token"
        
        mock_db = AsyncMock()
        
        with patch('src.core.auth.verify_token', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials, mock_db)
                
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid authentication credentials" in str(exc_info.value.detail)
            
    async def test_get_current_user_not_found(self):
        """Test getting current user when user not found in database."""
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid_token"
        
        mock_db = AsyncMock()
        
        mock_token_payload = Mock()
        mock_token_payload.sub = "999"
        
        with patch('src.core.auth.verify_token', return_value=mock_token_payload):
            with patch('src.core.auth.UserRepository') as mock_repo_class:
                mock_repo = mock_repo_class.return_value
                mock_repo.get = AsyncMock(return_value=None)
                
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(mock_credentials, mock_db)
                    
                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
                assert "User not found" in str(exc_info.value.detail)
                
    async def test_get_current_user_inactive(self):
        """Test getting current user when user is inactive."""
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid_token"
        
        mock_db = AsyncMock()
        
        mock_user = User(
            id=1,
            email="inactive@example.com",
            username="inactive",
            full_name="Inactive User",
            hashed_password="hashed",
            role=UserRole.VIEWER,
            is_active=False,
            is_verified=True
        )
        
        mock_token_payload = Mock()
        mock_token_payload.sub = "1"
        
        with patch('src.core.auth.verify_token', return_value=mock_token_payload):
            with patch('src.core.auth.UserRepository') as mock_repo_class:
                mock_repo = mock_repo_class.return_value
                mock_repo.get = AsyncMock(return_value=mock_user)
                
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(mock_credentials, mock_db)
                    
                assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
                assert "Inactive user" in str(exc_info.value.detail)
                
    async def test_get_current_active_user_success(self):
        """Test getting current active user."""
        mock_user = User(
            id=1,
            email="active@example.com",
            username="active",
            full_name="Active User",
            hashed_password="hashed",
            role=UserRole.VIEWER,
            is_active=True,
            is_verified=True
        )
        
        result = await get_current_active_user(mock_user)
        assert result == mock_user
        
    async def test_get_current_active_user_inactive(self):
        """Test getting current active user when user is inactive."""
        mock_user = User(
            id=1,
            email="inactive@example.com",
            username="inactive",
            full_name="Inactive User",
            hashed_password="hashed",
            role=UserRole.VIEWER,
            is_active=False,
            is_verified=True
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(mock_user)
            
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Inactive user" in str(exc_info.value.detail)
        
    async def test_require_role_allowed(self):
        """Test role requirement when user has allowed role."""
        allowed_roles = ["admin", "analyst"]
        role_checker = require_role(allowed_roles)
        
        mock_user = User(
            id=1,
            email="admin@example.com",
            username="admin",
            full_name="Admin User",
            hashed_password="hashed",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        result = await role_checker(mock_user)
        assert result == mock_user
        
    async def test_require_role_not_allowed(self):
        """Test role requirement when user doesn't have allowed role."""
        allowed_roles = ["admin", "analyst"]
        role_checker = require_role(allowed_roles)
        
        mock_user = User(
            id=1,
            email="viewer@example.com",
            username="viewer",
            full_name="Viewer User",
            hashed_password="hashed",
            role=UserRole.VIEWER,
            is_active=True,
            is_verified=True
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await role_checker(mock_user)
            
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "not in allowed roles" in str(exc_info.value.detail)
        
    async def test_get_admin_user_success(self):
        """Test getting admin user with admin role."""
        mock_user = User(
            id=1,
            email="admin@example.com",
            username="admin",
            full_name="Admin User",
            hashed_password="hashed",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        # Since get_admin_user uses require_role dependency,
        # we just test that it correctly applies the admin role check
        result = await get_admin_user(mock_user)
        assert result == mock_user
                
    async def test_get_analyst_user_success(self):
        """Test getting analyst user with analyst role."""
        mock_user = User(
            id=1,
            email="analyst@example.com",
            username="analyst",
            full_name="Analyst User",
            hashed_password="hashed",
            role=UserRole.ANALYST,
            is_active=True,
            is_verified=True
        )
        
        # Since get_analyst_user uses require_role dependency,
        # we just test that it correctly applies the analyst role check
        result = await get_analyst_user(mock_user)
        assert result == mock_user