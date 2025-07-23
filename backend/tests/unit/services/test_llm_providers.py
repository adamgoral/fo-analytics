"""Tests for LLM provider implementations."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import Response
from pydantic import BaseModel

from services.llm import (
    AnthropicProvider,
    GeminiProvider,
    LLMConfig,
    LLMProviderFactory,
    LLMProviderType,
    LLMResponse,
    OpenAIProvider,
)


class TestModel(BaseModel):
    """Test model for structured responses."""
    
    name: str
    value: int
    description: str


class TestLLMProviderFactory:
    """Test the LLM provider factory."""
    
    def test_create_anthropic_provider(self):
        """Test creating an Anthropic provider."""
        config = LLMConfig(
            provider=LLMProviderType.ANTHROPIC,
            api_key="test-key",
            model="claude-3-5-sonnet-20241022",
        )
        provider = LLMProviderFactory.create(config)
        assert isinstance(provider, AnthropicProvider)
        assert provider.config == config
    
    def test_create_openai_provider(self):
        """Test creating an OpenAI provider."""
        config = LLMConfig(
            provider=LLMProviderType.OPENAI,
            api_key="test-key",
            model="gpt-4o",
        )
        provider = LLMProviderFactory.create(config)
        assert isinstance(provider, OpenAIProvider)
        assert provider.config == config
    
    def test_create_gemini_provider(self):
        """Test creating a Gemini provider."""
        config = LLMConfig(
            provider=LLMProviderType.GEMINI,
            api_key="test-key",
            model="gemini-1.5-pro",
        )
        provider = LLMProviderFactory.create(config)
        assert isinstance(provider, GeminiProvider)
        assert provider.config == config
    
    def test_get_available_providers(self):
        """Test getting available providers."""
        providers = LLMProviderFactory.get_available_providers()
        assert "anthropic" in providers
        assert "openai" in providers
        assert "gemini" in providers


class TestAnthropicProvider:
    """Test the Anthropic provider implementation."""
    
    @pytest.fixture
    def provider(self):
        """Create an Anthropic provider instance."""
        config = LLMConfig(
            provider=LLMProviderType.ANTHROPIC,
            api_key="test-key",
            model="claude-3-5-sonnet-20241022",
            temperature=0.7,
            max_tokens=1000,
        )
        return AnthropicProvider(config)
    
    def test_validate_config_valid_model(self, provider):
        """Test config validation with valid model."""
        # Should not raise
        provider._validate_config()
    
    def test_validate_config_invalid_model(self):
        """Test config validation with invalid model."""
        config = LLMConfig(
            provider=LLMProviderType.ANTHROPIC,
            api_key="test-key",
            model="invalid-model",
        )
        with pytest.raises(ValueError, match="Invalid Anthropic model"):
            AnthropicProvider(config)
    
    def test_validate_config_no_api_key(self):
        """Test config validation without API key."""
        config = LLMConfig(
            provider=LLMProviderType.ANTHROPIC,
            api_key="",
            model="claude-3-5-sonnet-20241022",
        )
        with pytest.raises(ValueError, match="API key is required"):
            AnthropicProvider(config)
    
    @pytest.mark.asyncio
    async def test_generate(self, provider):
        """Test generating a response."""
        mock_response = {
            "id": "msg_123",
            "model": "claude-3-5-sonnet-20241022",
            "content": [{"text": "Test response"}],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 20,
            },
            "stop_reason": "end_turn",
        }
        
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = AsyncMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            )
            
            response = await provider.generate(
                prompt="Test prompt",
                system_prompt="Test system",
            )
            
            assert isinstance(response, LLMResponse)
            assert response.content == "Test response"
            assert response.model == "claude-3-5-sonnet-20241022"
            assert response.provider == LLMProviderType.ANTHROPIC
            assert response.usage["total_tokens"] == 30
            
            # Check API call
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args.args[0] == provider.API_URL
            assert call_args.kwargs["headers"]["x-api-key"] == "test-key"
            
            payload = call_args.kwargs["json"]
            assert payload["model"] == "claude-3-5-sonnet-20241022"
            assert payload["system"] == "Test system"
            assert payload["messages"][0]["content"] == "Test prompt"
    
    @pytest.mark.asyncio
    async def test_generate_structured(self, provider):
        """Test generating a structured response."""
        mock_response = {
            "id": "msg_123",
            "model": "claude-3-5-sonnet-20241022",
            "content": [{
                "text": '{"name": "test", "value": 42, "description": "A test"}'
            }],
            "usage": {
                "input_tokens": 50,
                "output_tokens": 30,
            },
        }
        
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = AsyncMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            )
            
            model, response = await provider.generate_structured(
                prompt="Generate test data",
                response_model=TestModel,
            )
            
            assert isinstance(model, TestModel)
            assert model.name == "test"
            assert model.value == 42
            assert model.description == "A test"
            assert response.usage["total_tokens"] == 80
    
    @pytest.mark.asyncio
    async def test_stream_generate(self, provider):
        """Test streaming responses."""
        stream_data = [
            'data: {"type": "content_block_delta", "delta": {"text": "Hello"}}',
            'data: {"type": "content_block_delta", "delta": {"text": " world"}}',
            'data: [DONE]',
        ]
        
        async def mock_aiter_lines():
            for line in stream_data:
                yield line
        
        mock_response = AsyncMock()
        mock_response.aiter_lines = mock_aiter_lines
        mock_response.raise_for_status = lambda: None
        
        with patch("httpx.AsyncClient.stream") as mock_stream:
            mock_stream.return_value.__aenter__.return_value = mock_response
            
            chunks = []
            async for chunk in provider.stream_generate("Test prompt"):
                chunks.append(chunk)
            
            assert chunks == ["Hello", " world"]


class TestOpenAIProvider:
    """Test the OpenAI provider implementation."""
    
    @pytest.fixture
    def provider(self):
        """Create an OpenAI provider instance."""
        config = LLMConfig(
            provider=LLMProviderType.OPENAI,
            api_key="test-key",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=1000,
        )
        return OpenAIProvider(config)
    
    def test_validate_config_valid_models(self):
        """Test config validation with various valid models."""
        valid_models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo-2024-04-09"]
        
        for model in valid_models:
            config = LLMConfig(
                provider=LLMProviderType.OPENAI,
                api_key="test-key",
                model=model,
            )
            provider = OpenAIProvider(config)
            provider._validate_config()  # Should not raise
    
    @pytest.mark.asyncio
    async def test_generate(self, provider):
        """Test generating a response."""
        mock_response = {
            "id": "chatcmpl-123",
            "model": "gpt-4o",
            "created": 1234567890,
            "choices": [{
                "message": {"content": "Test response"},
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        }
        
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = AsyncMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            )
            
            response = await provider.generate(
                prompt="Test prompt",
                system_prompt="Test system",
            )
            
            assert response.content == "Test response"
            assert response.model == "gpt-4o"
            assert response.provider == LLMProviderType.OPENAI
            assert response.usage["total_tokens"] == 30
            
            # Check API call
            call_args = mock_post.call_args
            assert "Authorization" in call_args.kwargs["headers"]
            assert call_args.kwargs["headers"]["Authorization"] == "Bearer test-key"
    
    @pytest.mark.asyncio
    async def test_generate_structured_with_json_mode(self, provider):
        """Test structured generation with JSON mode support."""
        mock_response = {
            "id": "chatcmpl-123",
            "model": "gpt-4o",
            "choices": [{
                "message": {
                    "content": '{"name": "test", "value": 42, "description": "A test"}'
                },
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 30,
                "total_tokens": 80,
            },
        }
        
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = AsyncMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            )
            
            model, response = await provider.generate_structured(
                prompt="Generate test data",
                response_model=TestModel,
            )
            
            assert isinstance(model, TestModel)
            assert model.name == "test"
            
            # Check that JSON mode was enabled
            call_args = mock_post.call_args
            payload = call_args.kwargs["json"]
            assert payload["response_format"] == {"type": "json_object"}


class TestGeminiProvider:
    """Test the Gemini provider implementation."""
    
    @pytest.fixture
    def provider(self):
        """Create a Gemini provider instance."""
        config = LLMConfig(
            provider=LLMProviderType.GEMINI,
            api_key="test-key",
            model="gemini-1.5-pro",
            temperature=0.7,
            max_tokens=1000,
        )
        return GeminiProvider(config)
    
    def test_get_url(self, provider):
        """Test URL construction."""
        url = provider._get_url("generateContent")
        expected = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-1.5-pro:generateContent?key=test-key"
        )
        assert url == expected
    
    def test_convert_messages_to_gemini_format(self, provider):
        """Test message format conversion."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
            {"role": "assistant", "content": "Assistant response"},
        ]
        
        system, contents = provider._convert_messages_to_gemini_format(messages)
        
        assert system == "System prompt"
        assert len(contents) == 2
        assert contents[0]["role"] == "user"
        assert contents[0]["parts"][0]["text"] == "User message"
        assert contents[1]["role"] == "model"
        assert contents[1]["parts"][0]["text"] == "Assistant response"
    
    @pytest.mark.asyncio
    async def test_generate(self, provider):
        """Test generating a response."""
        mock_response = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "Test response"}],
                },
                "finishReason": "STOP",
                "safetyRatings": [],
            }],
            "usageMetadata": {
                "promptTokenCount": 10,
                "candidatesTokenCount": 20,
                "totalTokenCount": 30,
            },
        }
        
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = AsyncMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            )
            
            response = await provider.generate(
                prompt="Test prompt",
                system_prompt="Test system",
            )
            
            assert response.content == "Test response"
            assert response.model == "gemini-1.5-pro"
            assert response.provider == LLMProviderType.GEMINI
            assert response.usage["total_tokens"] == 30
            
            # Check API call structure
            call_args = mock_post.call_args
            payload = call_args.kwargs["json"]
            assert "systemInstruction" in payload
            assert payload["systemInstruction"]["parts"][0]["text"] == "Test system"