"""Tests for the high-level LLM service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.config import Settings
from services.llm import LLMConfig, LLMProviderType, LLMResponse, LLMService
from services.llm.providers import AnthropicProvider


class TestLLMService:
    """Test the LLM service."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock(spec=Settings)
        settings.llm_provider = "anthropic"
        settings.llm_model = "claude-3-5-sonnet-20241022"
        settings.llm_temperature = 0.7
        settings.llm_max_tokens = 4096
        settings.llm_timeout = 60
        settings.anthropic_api_key = "test-anthropic-key"
        settings.openai_api_key = "test-openai-key"
        settings.google_api_key = "test-google-key"
        return settings
    
    @pytest.fixture
    def mock_provider(self):
        """Create a mock LLM provider."""
        provider = AsyncMock()
        provider.config = LLMConfig(
            provider=LLMProviderType.ANTHROPIC,
            api_key="test-key",
            model="claude-3-5-sonnet-20241022",
        )
        return provider
    
    def test_init_with_provider(self, mock_provider):
        """Test initialization with a pre-configured provider."""
        service = LLMService(provider=mock_provider)
        assert service.provider == mock_provider
    
    @patch("services.llm.service.settings")
    @patch("services.llm.service.LLMProviderFactory")
    def test_init_from_settings_anthropic(self, mock_factory, mock_settings_patch, mock_settings):
        """Test initialization from settings with Anthropic."""
        # Configure the mocked settings
        for attr, value in vars(mock_settings).items():
            setattr(mock_settings_patch, attr, value)
        
        mock_provider = MagicMock()
        mock_factory.create.return_value = mock_provider
        
        service = LLMService()
        
        # Verify factory was called with correct config
        mock_factory.create.assert_called_once()
        config = mock_factory.create.call_args[0][0]
        assert config.provider == LLMProviderType.ANTHROPIC
        assert config.api_key == "test-anthropic-key"
        assert config.model == "claude-3-5-sonnet-20241022"
        assert service.provider == mock_provider
    
    @patch("services.llm.service.settings")
    @patch("services.llm.service.LLMProviderFactory")
    def test_init_from_settings_openai(self, mock_factory, mock_settings_patch, mock_settings):
        """Test initialization from settings with OpenAI."""
        mock_settings.llm_provider = "openai"
        mock_settings.llm_model = "gpt-4o"
        
        for attr, value in vars(mock_settings).items():
            setattr(mock_settings_patch, attr, value)
        
        mock_provider = MagicMock()
        mock_factory.create.return_value = mock_provider
        
        service = LLMService()
        
        config = mock_factory.create.call_args[0][0]
        assert config.provider == LLMProviderType.OPENAI
        assert config.api_key == "test-openai-key"
        assert config.model == "gpt-4o"
    
    @patch("services.llm.service.settings")
    @patch("services.llm.service.LLMProviderFactory")
    def test_init_from_settings_gemini(self, mock_factory, mock_settings_patch, mock_settings):
        """Test initialization from settings with Gemini."""
        mock_settings.llm_provider = "gemini"
        mock_settings.llm_model = "gemini-1.5-pro"
        
        for attr, value in vars(mock_settings).items():
            setattr(mock_settings_patch, attr, value)
        
        mock_provider = MagicMock()
        mock_factory.create.return_value = mock_provider
        
        service = LLMService()
        
        config = mock_factory.create.call_args[0][0]
        assert config.provider == LLMProviderType.GEMINI
        assert config.api_key == "test-google-key"
        assert config.model == "gemini-1.5-pro"
    
    @patch("services.llm.service.settings")
    def test_init_invalid_provider(self, mock_settings_patch, mock_settings):
        """Test initialization with invalid provider."""
        mock_settings.llm_provider = "invalid_provider"
        
        for attr, value in vars(mock_settings).items():
            setattr(mock_settings_patch, attr, value)
        
        with pytest.raises(ValueError, match="Invalid LLM provider"):
            LLMService()
    
    @patch("services.llm.service.settings")
    def test_init_missing_api_key(self, mock_settings_patch, mock_settings):
        """Test initialization with missing API key."""
        mock_settings.anthropic_api_key = None
        
        for attr, value in vars(mock_settings).items():
            setattr(mock_settings_patch, attr, value)
        
        with pytest.raises(ValueError, match="API key not configured"):
            LLMService()
    
    @pytest.mark.asyncio
    async def test_extract_strategy(self, mock_provider):
        """Test strategy extraction from document."""
        mock_response = LLMResponse(
            content="Extracted strategy content",
            model="claude-3-5-sonnet-20241022",
            provider=LLMProviderType.ANTHROPIC,
            usage={"input_tokens": 100, "output_tokens": 200, "total_tokens": 300},
        )
        
        mock_provider.generate.return_value = mock_response
        
        service = LLMService(provider=mock_provider)
        result = await service.extract_strategy("Test document content")
        
        assert result["strategy_analysis"] == "Extracted strategy content"
        assert result["metadata"]["model"] == "claude-3-5-sonnet-20241022"
        assert result["metadata"]["provider"] == "anthropic"
        assert result["metadata"]["tokens"]["total_tokens"] == 300
        
        # Verify the prompt was constructed correctly
        mock_provider.generate.assert_called_once()
        call_args = mock_provider.generate.call_args
        assert "Test document content" in call_args.kwargs["prompt"]
        assert "financial analyst" in call_args.kwargs["system_prompt"]
    
    def test_get_provider_info(self, mock_provider):
        """Test getting provider information."""
        mock_provider.config.provider = LLMProviderType.ANTHROPIC
        mock_provider.config.model = "claude-3-5-sonnet-20241022"
        mock_provider.config.temperature = 0.7
        mock_provider.config.max_tokens = 4096
        
        service = LLMService(provider=mock_provider)
        info = service.get_provider_info()
        
        assert info["provider"] == "anthropic"
        assert info["model"] == "claude-3-5-sonnet-20241022"
        assert info["temperature"] == 0.7
        assert info["max_tokens"] == 4096