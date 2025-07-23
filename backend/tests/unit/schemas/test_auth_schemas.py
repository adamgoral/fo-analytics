"""Tests for authentication-related schemas."""

import pytest
from pydantic import ValidationError

from schemas.auth import UserLogin, TokenResponse, RefreshTokenRequest, ChangePasswordRequest, UserCreate, UserResponse


class TestAuthSchemas:
    """Test authentication schema validation."""
    
    def test_user_login_valid(self):
        """Test valid UserLogin schema."""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        
        login = UserLogin(**data)
        assert login.email == "test@example.com"
        assert login.password == "SecurePass123!"
    
    def test_user_login_invalid_email(self):
        """Test UserLogin with invalid email."""
        data = {
            "email": "not-an-email",
            "password": "SecurePass123!"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserLogin(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("email",) for error in errors)
    
    def test_user_login_missing_password(self):
        """Test UserLogin with missing password."""
        data = {
            "email": "test@example.com"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserLogin(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("password",) for error in errors)
    
    def test_token_response_schema(self):
        """Test TokenResponse schema."""
        user_data = {
            "id": 1,
            "full_name": "Test User",
            "username": "testuser",
            "email": "test@example.com",
            "role": "viewer",
            "is_active": True,
            "is_verified": True,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00"
        }
        data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ8...",
            "token_type": "bearer",
            "user": user_data
        }
        
        token = TokenResponse(**data)
        assert token.access_token == data["access_token"]
        assert token.refresh_token == data["refresh_token"]
        assert token.token_type == "bearer"
        assert token.user.email == "test@example.com"
    
    def test_refresh_token_request_valid(self):
        """Test valid RefreshTokenRequest schema."""
        data = {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ8..."
        }
        
        refresh = RefreshTokenRequest(**data)
        assert refresh.refresh_token == data["refresh_token"]
    
    def test_change_password_request_valid(self):
        """Test valid ChangePasswordRequest schema."""
        data = {
            "current_password": "OldPassword123!",
            "new_password": "NewPassword456!"
        }
        
        change = ChangePasswordRequest(**data)
        assert change.current_password == "OldPassword123!"
        assert change.new_password == "NewPassword456!"
    
    def test_change_password_request_short_new_password(self):
        """Test ChangePasswordRequest with short new password."""
        data = {
            "current_password": "OldPassword123!",
            "new_password": "short"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ChangePasswordRequest(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("new_password",) for error in errors)
    
    def test_user_create_valid(self):
        """Test valid UserCreate schema."""
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