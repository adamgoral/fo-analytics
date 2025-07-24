"""Tests for LLM provider factory."""

import pytest
from unittest.mock import Mock, patch

from src.services.llm.factory import LLMProviderFactory, LLMProvider
from src.services.llm.providers.anthropic import AnthropicProvider
from src.services.llm.providers.openai import OpenAIProvider
from src.services.llm.providers.gemini import GeminiProvider
from src.core.config import settings


class TestLLMProviderFactory:
    """Test LLM provider factory functionality."""
    
    def test_create_anthropic_provider(self):
        """Test creating Anthropic provider."""
        with patch.object(settings, 'anthropic_api_key', 'test-anthropic-key'):
            provider = LLMProviderFactory.create_provider(LLMProvider.ANTHROPIC)
            assert isinstance(provider, AnthropicProvider)
    
    def test_create_openai_provider(self):
        """Test creating OpenAI provider."""
        with patch.object(settings, 'openai_api_key', 'test-openai-key'):
            provider = LLMProviderFactory.create_provider(LLMProvider.OPENAI)
            assert isinstance(provider, OpenAIProvider)
    
    def test_create_gemini_provider(self):
        """Test creating Gemini provider."""
        with patch.object(settings, 'google_api_key', 'test-google-key'):
            provider = LLMProviderFactory.create_provider(LLMProvider.GEMINI)
            assert isinstance(provider, GeminiProvider)
    
    def test_create_provider_missing_api_key(self):
        """Test creating provider without API key raises error."""
        with patch.object(settings, 'anthropic_api_key', None):
            with pytest.raises(ValueError) as exc_info:
                LLMProviderFactory.create_provider(LLMProvider.ANTHROPIC)
            assert "API key not found for provider: anthropic" in str(exc_info.value)
    
    def test_create_provider_invalid_type(self):
        """Test creating provider with invalid type."""
        with pytest.raises(ValueError) as exc_info:
            LLMProviderFactory.create_provider("invalid_provider")
        assert "Unsupported provider: invalid_provider" in str(exc_info.value)
    
    def test_get_available_providers_all_configured(self):
        """Test getting available providers when all are configured."""
        with patch.object(settings, 'anthropic_api_key', 'test-key'):
            with patch.object(settings, 'openai_api_key', 'test-key'):
                with patch.object(settings, 'google_api_key', 'test-key'):
                    providers = LLLProviderFactory.get_available_providers()
                    assert len(providers) == 3
                    assert LLMProvider.ANTHROPIC in providers
                    assert LLMProvider.OPENAI in providers
                    assert LLMProvider.GEMINI in providers
    
    def test_get_available_providers_partial_configured(self):
        """Test getting available providers when only some are configured."""
        with patch.object(settings, 'anthropic_api_key', 'test-key'):
            with patch.object(settings, 'openai_api_key', None):
                with patch.object(settings, 'google_api_key', 'test-key'):
                    providers = LLMProviderFactory.get_available_providers()
                    assert len(providers) == 2
                    assert LLMProvider.ANTHROPIC in providers
                    assert LLMProvider.OPENAI not in providers
                    assert LLMProvider.GEMINI in providers
    
    def test_get_available_providers_none_configured(self):
        """Test getting available providers when none are configured."""
        with patch.object(settings, 'anthropic_api_key', None):
            with patch.object(settings, 'openai_api_key', None):
                with patch.object(settings, 'google_api_key', None):
                    providers = LLMProviderFactory.get_available_providers()
                    assert len(providers) == 0
    
    def test_create_provider_with_custom_config(self):
        """Test creating provider with custom configuration."""
        with patch.object(settings, 'anthropic_api_key', 'test-key'):
            custom_config = {
                "model": "claude-3-opus",
                "temperature": 0.5,
                "max_tokens": 2000
            }
            
            with patch('src.services.llm.providers.anthropic.AnthropicProvider.__init__', return_value=None) as mock_init:
                LLMProviderFactory.create_provider(LLMProvider.ANTHROPIC, config=custom_config)
                mock_init.assert_called_once_with(api_key='test-key', config=custom_config)
    
    def test_provider_singleton_pattern(self):
        """Test that factory can implement singleton pattern for providers."""
        with patch.object(settings, 'anthropic_api_key', 'test-key'):
            # Clear any cached providers
            if hasattr(LLMProviderFactory, '_providers'):
                LLMProviderFactory._providers.clear()
            
            provider1 = LLMProviderFactory.create_provider(LLMProvider.ANTHROPIC)
            provider2 = LLMProviderFactory.create_provider(LLMProvider.ANTHROPIC)
            
            # Should create new instances (not singleton by default)
            assert provider1 is not provider2
    
    def test_create_provider_with_retry_config(self):
        """Test creating provider with retry configuration."""
        with patch.object(settings, 'openai_api_key', 'test-key'):
            with patch.object(settings, 'llm_retry_attempts', 5):
                with patch.object(settings, 'llm_retry_delay', 2.0):
                    provider = LLMProviderFactory.create_provider(LLMProvider.OPENAI)
                    # Provider should be created successfully with retry config from settings
                    assert isinstance(provider, OpenAIProvider)