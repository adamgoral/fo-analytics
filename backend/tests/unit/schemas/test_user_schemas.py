"""Tests for user-related schemas."""

import pytest
from pydantic import ValidationError

from schemas.auth import UserCreate, UserResponse
from models.user import UserRole


class TestUserSchemas:
    """Test user schema validation."""
    
    def test_user_create_valid(self):
        """Test creating valid UserCreate schema."""
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "role": "analyst"
        }
        
        user = UserCreate(**data)
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.password == "SecurePass123!"
        assert user.role == "analyst"
    
    def test_user_create_invalid_email(self):
        """Test UserCreate with invalid email."""
        data = {
            "name": "Test User",
            "email": "not-an-email",
            "password": "SecurePass123!"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("email",) for error in errors)
    
    def test_user_create_short_password(self):
        """Test UserCreate with short password."""
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "short"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("password",) for error in errors)
    
    def test_user_create_missing_required_fields(self):
        """Test UserCreate with missing required fields."""
        data = {
            "email": "test@example.com"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)
        
        errors = exc_info.value.errors()
        assert len(errors) >= 2  # Missing name, password
    
    def test_user_create_invalid_role(self):
        """Test UserCreate with invalid role."""
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "role": "superadmin"  # Invalid role
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("role",) for error in errors)
    
    def test_user_response(self):
        """Test UserResponse schema."""
        data = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "is_active": True,
            "is_verified": False,
            "role": UserRole.VIEWER,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00"
        }
        
        response = UserResponse(**data)
        assert response.id == 1
        assert response.email == "test@example.com"
        assert response.username == "testuser"
        assert response.full_name == "Test User"
        assert response.is_active is True
        assert response.is_verified is False
        assert response.role == "viewer"
    
