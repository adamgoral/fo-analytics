"""Tests for configuration module."""

import os
import pytest
from unittest.mock import patch

from core.config import Settings, settings


class TestConfig:
    """Test configuration settings."""
    
    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()
        
        # Check default values
        assert settings.app_name == "Front Office Analytics Platform"
        assert settings.app_version == "0.1.0"
        assert settings.debug is False
        assert settings.testing is False
        
        # Database defaults
        assert settings.database_url == "postgresql+asyncpg://fo_user:fo_password@localhost:5432/fo_analytics"
        
        # Redis defaults
        assert settings.redis_url == "redis://localhost:6379/0"
        
        # JWT defaults
        assert settings.secret_key == "your-secret-key-here"
        assert settings.algorithm == "HS256"
        assert settings.access_token_expire_minutes == 30
        assert settings.refresh_token_expire_days == 7
        
        # CORS defaults
        assert settings.cors_origins == ["http://localhost:3000", "http://localhost:5173"]
        # CORS settings are not in the Settings class
    
    def test_settings_from_env(self):
        """Test loading settings from environment variables."""
        env_vars = {
            "APP_NAME": "Test App",
            "APP_VERSION": "2.0.0",
            "DEBUG": "true",
            "TESTING": "true",
            "DATABASE_URL": "postgresql+asyncpg://test:test@testhost:5432/testdb",
            "REDIS_URL": "redis://testhost:6379/1",
            "SECRET_KEY": "test-secret-key",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
            "REFRESH_TOKEN_EXPIRE_DAYS": "14"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            assert settings.app_name == "Test App"
            assert settings.app_version == "2.0.0"
            assert settings.debug is True
            assert settings.testing is True
            assert settings.database_url == "postgresql+asyncpg://test:test@testhost:5432/testdb"
            assert settings.redis_url == "redis://testhost:6379/1"
            assert settings.secret_key == "test-secret-key"
            assert settings.access_token_expire_minutes == 60
            assert settings.refresh_token_expire_days == 14
    
    def test_cors_origins_from_string(self):
        """Test parsing CORS origins from comma-separated string."""
        env_vars = {
            "CORS_ORIGINS": "http://localhost:3000,http://localhost:3001,https://example.com"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            assert settings.cors_origins == [
                "http://localhost:3000",
                "http://localhost:3001",
                "https://example.com"
            ]
    
    def test_cors_origins_from_json(self):
        """Test parsing CORS origins from JSON string."""
        env_vars = {
            "CORS_ORIGINS": '["http://localhost:3000", "https://example.com"]'
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            assert settings.cors_origins == [
                "http://localhost:3000",
                "https://example.com"
            ]
    
    def test_settings_instance(self):
        """Test that settings is a singleton instance."""
        from core.config import settings
        
        assert settings is not None
        assert isinstance(settings, Settings)
        assert settings.app_name == "Front Office Analytics Platform"