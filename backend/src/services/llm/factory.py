"""Factory for creating LLM provider instances."""

from typing import Dict, Type

from .base import LLMConfig, LLMProvider, LLMProviderType
from .providers import AnthropicProvider, GeminiProvider, OpenAIProvider


class LLMProviderFactory:
    """Factory class for creating LLM provider instances."""
    
    _providers: Dict[LLMProviderType, Type[LLMProvider]] = {
        LLMProviderType.ANTHROPIC: AnthropicProvider,
        LLMProviderType.OPENAI: OpenAIProvider,
        LLMProviderType.GEMINI: GeminiProvider,
    }
    
    @classmethod
    def create(cls, config: LLMConfig) -> LLMProvider:
        """Create an LLM provider instance based on configuration.
        
        Args:
            config: LLM configuration object
            
        Returns:
            Configured LLM provider instance
            
        Raises:
            ValueError: If provider type is not supported
        """
        provider_class = cls._providers.get(config.provider)
        if not provider_class:
            raise ValueError(
                f"Unsupported provider: {config.provider}. "
                f"Supported providers: {', '.join(p.value for p in LLMProviderType)}"
            )
        
        return provider_class(config)
    
    @classmethod
    def register_provider(
        cls,
        provider_type: LLMProviderType,
        provider_class: Type[LLMProvider]
    ) -> None:
        """Register a custom provider implementation.
        
        Args:
            provider_type: The provider type identifier
            provider_class: The provider implementation class
        """
        cls._providers[provider_type] = provider_class
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider types.
        
        Returns:
            List of provider type names
        """
        return [p.value for p in cls._providers.keys()]