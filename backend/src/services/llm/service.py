"""High-level LLM service for strategy extraction."""

from typing import Optional

from core.config import settings
from core.logging_config import get_logger

from .base import LLMConfig, LLMProvider, LLMProviderType
from .factory import LLMProviderFactory

logger = get_logger(__name__)


class LLMService:
    """Service for managing LLM operations."""
    
    def __init__(self, provider: Optional[LLMProvider] = None):
        """Initialize the LLM service.
        
        Args:
            provider: Optional pre-configured LLM provider.
                     If not provided, will create from settings.
        """
        if provider:
            self.provider = provider
        else:
            self.provider = self._create_provider_from_settings()
    
    def _create_provider_from_settings(self) -> LLMProvider:
        """Create an LLM provider from application settings."""
        # Map provider names to enum values
        provider_map = {
            "anthropic": LLMProviderType.ANTHROPIC,
            "openai": LLMProviderType.OPENAI,
            "gemini": LLMProviderType.GEMINI,
        }
        
        provider_type = provider_map.get(settings.llm_provider.lower())
        if not provider_type:
            raise ValueError(
                f"Invalid LLM provider in settings: {settings.llm_provider}. "
                f"Valid options: {', '.join(provider_map.keys())}"
            )
        
        # Get the appropriate API key
        api_key = None
        if provider_type == LLMProviderType.ANTHROPIC:
            api_key = settings.anthropic_api_key
        elif provider_type == LLMProviderType.OPENAI:
            api_key = settings.openai_api_key
        elif provider_type == LLMProviderType.GEMINI:
            api_key = settings.google_api_key
        
        if not api_key:
            raise ValueError(
                f"API key not configured for provider: {settings.llm_provider}. "
                f"Please set the appropriate environment variable."
            )
        
        # Create configuration
        config = LLMConfig(
            provider=provider_type,
            api_key=api_key,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            timeout=settings.llm_timeout,
        )
        
        logger.info(
            "Creating LLM provider",
            extra={
                "provider": provider_type.value,
                "model": settings.llm_model,
                "temperature": settings.llm_temperature,
                "max_tokens": settings.llm_max_tokens,
            }
        )
        
        return LLMProviderFactory.create(config)
    
    async def extract_strategy(self, document_content: str) -> dict:
        """Extract trading strategy from document content.
        
        Args:
            document_content: The parsed document text
            
        Returns:
            Dictionary containing extracted strategy information
        """
        system_prompt = """You are a financial analyst AI assistant specialized in extracting trading strategies from research documents.

Your task is to analyze financial research documents and extract actionable trading strategies, including:
- Strategy description and rationale
- Target securities or asset classes
- Entry and exit conditions
- Risk management parameters
- Time horizon and expected returns

Focus on quantifiable and implementable strategies that can be backtested."""

        prompt = f"""Analyze the following financial research document and extract any trading strategies mentioned:

{document_content}

Please provide a structured analysis of the trading strategies found."""

        response = await self.provider.generate(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        logger.info(
            "Strategy extraction completed",
            extra={
                "content_length": len(document_content),
                "response_length": len(response.content),
                "tokens_used": response.usage,
            }
        )
        
        return {
            "strategy_analysis": response.content,
            "metadata": {
                "model": response.model,
                "provider": response.provider.value,
                "tokens": response.usage,
            }
        }
    
    def get_provider_info(self) -> dict:
        """Get information about the current LLM provider.
        
        Returns:
            Dictionary with provider details
        """
        return {
            "provider": self.provider.config.provider.value,
            "model": self.provider.config.model,
            "temperature": self.provider.config.temperature,
            "max_tokens": self.provider.config.max_tokens,
        }