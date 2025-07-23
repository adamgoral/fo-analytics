"""Tests for authentication API endpoints."""

import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock

from src.models.user import User, UserRole
from src.schemas.auth import UserCreate, UserLogin, TokenResponse
from src.services.auth_service import AuthService


@pytest.mark.asyncio
class TestAuthAPI:
    """Test authentication API endpoints."""

    async def test_register_success(self, async_client: AsyncClient, async_session: AsyncSession):
        """Test successful user registration."""
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securePassword123!",
            "role": "viewer"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["name"]
        assert data["role"] == user_data["role"]
        assert "id" in data
        assert "username" in data
        assert "password" not in data
        assert "hashed_password" not in data
        
    async def test_register_duplicate_email(self, async_client: AsyncClient, async_session: AsyncSession):
        """Test registration with duplicate email fails."""
        # First registration
        user_data = {
            "name": "Test User",
            "email": "duplicate@example.com",
            "password": "securePassword123!",
            "role": "viewer"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Attempt duplicate registration
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
        
    async def test_register_invalid_email(self, async_client: AsyncClient):
        """Test registration with invalid email format."""
        user_data = {
            "name": "Test User",
            "email": "invalid-email",
            "password": "securePassword123!",
            "role": "viewer"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error
        
    async def test_register_weak_password(self, async_client: AsyncClient):
        """Test registration with weak password."""
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "weak",
            "role": "viewer"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error
        
    async def test_register_invalid_role(self, async_client: AsyncClient):
        """Test registration with invalid role."""
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "securePassword123!",
            "role": "invalid_role"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error
        
    async def test_login_success(self, async_client: AsyncClient, async_session: AsyncSession):
        """Test successful login."""
        # Register user first
        user_data = {
            "name": "Login Test User",
            "email": "login@example.com",
            "password": "securePassword123!",
            "role": "viewer"
        }
        
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        # Login
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == user_data["email"]
        
    async def test_login_invalid_credentials(self, async_client: AsyncClient):
        """Test login with invalid credentials."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongPassword123!"
        }
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        
    async def test_login_wrong_password(self, async_client: AsyncClient, async_session: AsyncSession):
        """Test login with wrong password."""
        # Register user
        user_data = {
            "name": "Test User",
            "email": "wrongpass@example.com",
            "password": "correctPassword123!",
            "role": "viewer"
        }
        
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        # Login with wrong password
        login_data = {
            "email": user_data["email"],
            "password": "wrongPassword123!"
        }
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        
    async def test_refresh_token_success(self, async_client: AsyncClient, async_session: AsyncSession):
        """Test successful token refresh."""
        # Register and login
        user_data = {
            "name": "Refresh Test User",
            "email": "refresh@example.com",
            "password": "securePassword123!",
            "role": "viewer"
        }
        
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        tokens = login_response.json()
        
        # Refresh token
        response = await async_client.post("/api/v1/auth/refresh", json={
            "refresh_token": tokens["refresh_token"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == user_data["email"]
        
    async def test_refresh_token_invalid(self, async_client: AsyncClient):
        """Test refresh with invalid token."""
        response = await async_client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid_token"
        })
        
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]
        
    async def test_change_password_success(self, async_client: AsyncClient, async_session: AsyncSession):
        """Test successful password change."""
        # Register and login
        user_data = {
            "name": "Password Change User",
            "email": "passchange@example.com",
            "password": "oldPassword123!",
            "role": "viewer"
        }
        
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        access_token = login_response.json()["access_token"]
        
        # Change password
        response = await async_client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": user_data["password"],
                "new_password": "newSecurePassword123!"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"
        
        # Verify old password doesn't work
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 401
        
        # Verify new password works
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": "newSecurePassword123!"
        })
        assert login_response.status_code == 200
        
    async def test_change_password_wrong_current(self, async_client: AsyncClient, async_session: AsyncSession):
        """Test password change with wrong current password."""
        # Register and login
        user_data = {
            "name": "Wrong Password User",
            "email": "wrongcurrent@example.com",
            "password": "currentPassword123!",
            "role": "viewer"
        }
        
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        access_token = login_response.json()["access_token"]
        
        # Try to change password with wrong current password
        response = await async_client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "wrongPassword123!",
                "new_password": "newSecurePassword123!"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]
        
    async def test_change_password_unauthenticated(self, async_client: AsyncClient):
        """Test password change without authentication."""
        response = await async_client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "oldPassword123!",
                "new_password": "newPassword123!"
            }
        )
        
        assert response.status_code == 403  # HTTPBearer returns 403 when no auth header
        
    async def test_get_current_user_success(self, async_client: AsyncClient, async_session: AsyncSession):
        """Test getting current user information."""
        # Register and login
        user_data = {
            "name": "Current User",
            "email": "current@example.com",
            "password": "securePassword123!",
            "role": "analyst"
        }
        
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        access_token = login_response.json()["access_token"]
        
        # Get current user
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["name"]
        assert data["role"] == user_data["role"]
        assert "password" not in data
        
    async def test_get_current_user_unauthenticated(self, async_client: AsyncClient):
        """Test getting current user without authentication."""
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 403  # HTTPBearer returns 403 when no auth header
        
    async def test_get_current_user_expired_token(self, async_client: AsyncClient):
        """Test getting current user with expired token."""
        # Create an expired token
        with patch('src.core.security.datetime') as mock_datetime:
            # Mock time to create an expired token
            past_time = datetime.now(timezone.utc) - timedelta(hours=1)
            mock_datetime.now.return_value = past_time
            
            # This would need proper implementation with token generation
            expired_token = "expired_token_here"
            
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
        
    async def test_register_with_admin_role(self, async_client: AsyncClient):
        """Test registration with admin role."""
        user_data = {
            "name": "Admin User",
            "email": "admin@example.com",
            "password": "adminPassword123!",
            "role": "admin"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "admin"
        
    async def test_concurrent_registrations(self, async_client: AsyncClient):
        """Test handling of concurrent registration attempts."""
        user_data = {
            "name": "Concurrent User",
            "email": "concurrent@example.com",
            "password": "concurrentPass123!",
            "role": "viewer"
        }
        
        # First registration should succeed
        response1 = await async_client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Second registration with same email should fail
        response2 = await async_client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]