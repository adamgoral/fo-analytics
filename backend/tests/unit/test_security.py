"""Tests for security utilities."""

import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from src.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    create_token_pair,
    TokenPayload,
    TokenData
)
from src.core.config import settings


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 20
        assert hashed.startswith("$2b$")  # bcrypt prefix
        
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password123!"
        hashed = get_password_hash(password)
        
        assert verify_password("wrong_password", hashed) is False
        
    def test_hash_different_each_time(self):
        """Test that hashing the same password produces different hashes."""
        password = "test_password123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestTokenCreation:
    """Test JWT token creation."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        subject = "123"
        role = "viewer"
        
        token = create_access_token(subject, role)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify token
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == subject
        assert payload["role"] == role
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
        
    def test_create_access_token_with_custom_expiry(self):
        """Test access token with custom expiration."""
        subject = "123"
        role = "admin"
        expires_delta = timedelta(minutes=15)
        
        token = create_access_token(subject, role, expires_delta)
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        # Check expiration is approximately 15 minutes from now
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = exp_time - now
        
        assert 14 < diff.total_seconds() / 60 < 16
        
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        subject = "456"
        role = "analyst"
        
        token = create_refresh_token(subject, role)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify token
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == subject
        assert payload["role"] == role
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload
        # Note: Current implementation doesn't include JTI in refresh tokens
        
    def test_create_token_pair(self):
        """Test creating access and refresh token pair."""
        user_id = "789"
        role = "admin"
        
        token_data = create_token_pair(user_id, role)
        
        assert isinstance(token_data, TokenData)
        assert token_data.token_type == "bearer"
        assert len(token_data.access_token) > 0
        assert len(token_data.refresh_token) > 0
        assert token_data.access_token != token_data.refresh_token


class TestTokenVerification:
    """Test JWT token verification."""
    
    def test_verify_valid_access_token(self):
        """Test verifying a valid access token."""
        subject = "123"
        role = "viewer"
        token = create_access_token(subject, role)
        
        payload = verify_token(token, token_type="access")
        
        assert isinstance(payload, TokenPayload)
        assert payload.sub == subject
        assert payload.role == role
        
    def test_verify_valid_refresh_token(self):
        """Test verifying a valid refresh token."""
        subject = "456"
        role = "admin"
        token = create_refresh_token(subject, role)
        
        payload = verify_token(token, token_type="refresh")
        
        assert isinstance(payload, TokenPayload)
        assert payload.sub == subject
        assert payload.role == role
        # Note: Current implementation doesn't include JTI in refresh tokens
        
    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = verify_token(invalid_token)
        assert payload is None
        
    def test_verify_expired_token(self):
        """Test verifying an expired token."""
        # Create a token that's already expired
        subject = "123"
        role = "viewer"
        expires_delta = timedelta(seconds=-1)  # Expired 1 second ago
        
        # Manually create expired token
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "role": role,
            "type": "access"
        }
        expired_token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        
        payload = verify_token(expired_token)
        assert payload is None
        
    def test_verify_wrong_token_type(self):
        """Test verifying token with wrong type."""
        # Create refresh token but verify as access token
        subject = "123"
        role = "viewer"
        refresh_token = create_refresh_token(subject, role)
        
        payload = verify_token(refresh_token, token_type="access")
        assert payload is None
        
    def test_verify_tampered_token(self):
        """Test verifying a tampered token."""
        subject = "123"
        role = "viewer"
        token = create_access_token(subject, role)
        
        # Tamper with the token by changing a character
        tampered = token[:-1] + 'X'
        
        payload = verify_token(tampered)
        assert payload is None
        
    def test_verify_token_wrong_secret(self):
        """Test verifying token signed with different secret."""
        subject = "123"
        role = "viewer"
        
        # Create token with different secret
        wrong_secret_token = jwt.encode(
            {
                "sub": subject,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
                "iat": datetime.now(timezone.utc),
                "role": role,
                "type": "access"
            },
            "wrong_secret_key",
            algorithm=settings.algorithm
        )
        
        payload = verify_token(wrong_secret_token)
        assert payload is None