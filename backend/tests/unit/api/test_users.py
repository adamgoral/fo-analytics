"""Tests for user management API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User, UserRole


@pytest.mark.asyncio
class TestUsersAPI:
    """Test user management API endpoints."""

    async def test_get_user_by_id(self, async_client: AsyncClient, async_session: AsyncSession):
        """Test getting a user by ID."""
        # Create a user directly in the database
        user = User(
            email="getuser@example.com",
            username="getuser",
            full_name="Get User Test",
            hashed_password="hashed",
            role=UserRole.VIEWER,
            is_active=True,
            is_verified=True
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)
        
        # Get the user via API
        response = await async_client.get(f"/api/v1/users/{user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["email"] == user.email
        assert data["username"] == user.username
        assert data["full_name"] == user.full_name
        assert data["is_active"] == user.is_active
        
    async def test_get_user_not_found(self, async_client: AsyncClient):
        """Test getting a non-existent user."""
        response = await async_client.get("/api/v1/users/99999")
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
        
    async def test_list_users(self, async_client: AsyncClient, async_session: AsyncSession):
        """Test listing all users."""
        # Create multiple users
        users = []
        for i in range(3):
            user = User(
                email=f"user{i}@example.com",
                username=f"user{i}",
                full_name=f"User {i}",
                hashed_password="hashed",
                role=UserRole.VIEWER,
                is_active=True,
                is_verified=True
            )
            async_session.add(user)
            users.append(user)
        
        await async_session.commit()
        
        # List users
        response = await async_client.get("/api/v1/users/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Check that all users are in the response
        emails = [u["email"] for u in data]
        for user in users:
            assert user.email in emails
            
    async def test_list_users_with_pagination(self, async_client: AsyncClient, async_session: AsyncSession):
        """Test listing users with pagination."""
        # Create 5 users
        for i in range(5):
            user = User(
                email=f"page{i}@example.com",
                username=f"page{i}",
                full_name=f"Page User {i}",
                hashed_password="hashed",
                role=UserRole.VIEWER,
                is_active=True,
                is_verified=True
            )
            async_session.add(user)
        
        await async_session.commit()
        
        # Get first page
        response = await async_client.get("/api/v1/users/?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Get second page
        response = await async_client.get("/api/v1/users/?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Get third page
        response = await async_client.get("/api/v1/users/?skip=4&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        
    async def test_list_active_users(self, async_client: AsyncClient, async_session: AsyncSession):
        """Test listing only active users."""
        # Create active and inactive users
        active_user = User(
            email="active@example.com",
            username="activeuser",
            full_name="Active User",
            hashed_password="hashed",
            role=UserRole.VIEWER,
            is_active=True,
            is_verified=True
        )
        inactive_user = User(
            email="inactive@example.com",
            username="inactiveuser",
            full_name="Inactive User",
            hashed_password="hashed",
            role=UserRole.VIEWER,
            is_active=False,
            is_verified=True
        )
        
        async_session.add(active_user)
        async_session.add(inactive_user)
        await async_session.commit()
        
        # List active users
        response = await async_client.get("/api/v1/users/active/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only contain active users
        emails = [u["email"] for u in data]
        assert "active@example.com" in emails
        assert "inactive@example.com" not in emails
        
        # All returned users should be active
        for user in data:
            assert user["is_active"] is True
            
    async def test_list_active_users_pagination(self, async_client: AsyncClient, async_session: AsyncSession):
        """Test pagination for active users endpoint."""
        # Create multiple active users
        for i in range(3):
            user = User(
                email=f"activetest{i}@example.com",
                username=f"activetest{i}",
                full_name=f"Active Test {i}",
                hashed_password="hashed",
                role=UserRole.VIEWER,
                is_active=True,
                is_verified=True
            )
            async_session.add(user)
        
        await async_session.commit()
        
        # Test with limit
        response = await async_client.get("/api/v1/users/active/?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2
        
    async def test_get_user_invalid_id_format(self, async_client: AsyncClient):
        """Test getting user with invalid ID format."""
        response = await async_client.get("/api/v1/users/invalid-id")
        
        # Should return 422 for validation error
        assert response.status_code == 422