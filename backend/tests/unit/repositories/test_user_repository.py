"""Tests for user repository."""

import pytest
from uuid import uuid4

from src.models.user import User
from src.repositories.user import UserRepository


@pytest.mark.asyncio
async def test_user_repository_create(async_session):
    """Test creating a user through repository."""
    repo = UserRepository(async_session)
    
    user = await repo.create(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed_password_123",
    )
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.full_name == "Test User"
    assert user.is_active is True


@pytest.mark.asyncio
async def test_user_repository_get_by_email(async_session):
    """Test getting user by email."""
    repo = UserRepository(async_session)
    
    # Create user
    created_user = await repo.create(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed_password_123",
    )
    
    # Get by email
    found_user = await repo.get_by_email("test@example.com")
    
    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.email == "test@example.com"


@pytest.mark.asyncio
async def test_user_repository_get_by_username(async_session):
    """Test getting user by username."""
    repo = UserRepository(async_session)
    
    # Create user
    created_user = await repo.create(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed_password_123",
    )
    
    # Get by username
    found_user = await repo.get_by_username("testuser")
    
    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.username == "testuser"


@pytest.mark.asyncio
async def test_user_repository_update(async_session):
    """Test updating a user."""
    repo = UserRepository(async_session)
    
    # Create user
    user = await repo.create(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed_password_123",
    )
    
    # Update user
    updated_user = await repo.update(
        user.id,
        full_name="Updated User Name",
    )
    
    assert updated_user is not None
    assert updated_user.full_name == "Updated User Name"
    assert updated_user.email == "test@example.com"  # Unchanged


@pytest.mark.asyncio
async def test_user_repository_deactivate(async_session):
    """Test deactivating a user."""
    repo = UserRepository(async_session)
    
    # Create user
    user = await repo.create(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed_password_123",
    )
    
    assert user.is_active is True
    
    # Deactivate user
    deactivated_user = await repo.deactivate_user(user.id)
    
    assert deactivated_user is not None
    assert deactivated_user.is_active is False


@pytest.mark.asyncio
async def test_user_repository_get_active_users(async_session):
    """Test getting active users."""
    repo = UserRepository(async_session)
    
    # Create active users
    await repo.create(
        email="active1@example.com",
        username="active1",
        full_name="Active User 1",
        hashed_password="hashed_password_123",
    )
    
    user2 = await repo.create(
        email="active2@example.com",
        username="active2",
        full_name="Active User 2",
        hashed_password="hashed_password_123",
    )
    
    # Deactivate one user
    await repo.deactivate_user(user2.id)
    
    # Get active users
    active_users = await repo.get_active_users()
    
    assert len(active_users) == 1
    assert active_users[0].email == "active1@example.com"