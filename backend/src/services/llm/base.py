"""Base classes and interfaces for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LLMProviderType(StrEnum):
    """Supported LLM provider types."""
    
    ANTHROPIC = auto()
    OPENAI = auto()
    GEMINI = auto()


class LLMConfig(BaseModel):
    """Configuration for LLM providers."""
    
    provider: LLMProviderType
    api_key: str
    model: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, gt=0)
    timeout: int = Field(default=60, gt=0)
    extra_params: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    
    content: str
    model: str
    provider: LLMProviderType
    usage: Dict[str, int]
    raw_response: Optional[Any] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: LLMConfig):
        """Initialize the provider with configuration."""
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider-specific configuration."""
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse object containing the generated text and metadata
        """
        pass
    
    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[BaseModel],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> tuple[BaseModel, LLMResponse]:
        """Generate a structured response matching a Pydantic model.
        
        Args:
            prompt: The user prompt
            response_model: Pydantic model class for the expected response
            system_prompt: Optional system prompt for context
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Tuple of (parsed model instance, raw LLM response)
        """
        pass
    
    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """Stream responses from the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            **kwargs: Additional provider-specific parameters
            
        Yields:
            String chunks of the response as they arrive
        """
        pass
    
    def _prepare_messages(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Prepare messages in a common format.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            
        Returns:
            List of message dictionaries
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages