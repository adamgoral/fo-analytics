"""OpenAI GPT LLM provider implementation."""

import json
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel

from ..base import LLMConfig, LLMProvider, LLMProviderType, LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI GPT API provider."""
    
    API_URL = "https://api.openai.com/v1/chat/completions"
    
    def _validate_config(self) -> None:
        """Validate OpenAI-specific configuration."""
        if not self.config.api_key:
            raise ValueError("OpenAI API key is required")
        
        valid_models = [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
        ]
        
        if not any(self.config.model.startswith(prefix) for prefix in valid_models):
            raise ValueError(
                f"Invalid OpenAI model: {self.config.model}. "
                f"Valid model prefixes: {', '.join(valid_models)}"
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers for OpenAI API."""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from GPT."""
        messages = self._prepare_messages(prompt, system_prompt)
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            **self.config.extra_params,
            **kwargs
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.API_URL,
                headers=self._get_headers(),
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
        
        choice = data["choices"][0]
        usage = data["usage"]
        
        return LLMResponse(
            content=choice["message"]["content"],
            model=data["model"],
            provider=LLMProviderType.OPENAI,
            usage={
                "input_tokens": usage["prompt_tokens"],
                "output_tokens": usage["completion_tokens"],
                "total_tokens": usage["total_tokens"]
            },
            raw_response=data,
            metadata={
                "finish_reason": choice.get("finish_reason"),
                "id": data.get("id"),
                "created": data.get("created")
            }
        )
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[BaseModel],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> tuple[BaseModel, LLMResponse]:
        """Generate a structured response using OpenAI's JSON mode."""
        # Use response_format for models that support it
        supports_json_mode = any(
            self.config.model.startswith(m) 
            for m in ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
        )
        
        schema = response_model.model_json_schema()
        enhanced_prompt = (
            f"{prompt}\n\n"
            f"Please respond with valid JSON matching this schema:\n"
            f"```json\n{json.dumps(schema, indent=2)}\n```"
        )
        
        if system_prompt:
            enhanced_system = (
                f"{system_prompt}\n\n"
                f"You must respond with valid JSON that matches the provided schema."
            )
        else:
            enhanced_system = "You must respond with valid JSON that matches the provided schema."
        
        extra_kwargs = kwargs.copy()
        if supports_json_mode:
            extra_kwargs["response_format"] = {"type": "json_object"}
        
        response = await self.generate(
            enhanced_prompt,
            system_prompt=enhanced_system,
            **extra_kwargs
        )
        
        # Parse the JSON response
        try:
            parsed_data = json.loads(response.content)
            model_instance = response_model.model_validate(parsed_data)
            return model_instance, response
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to parse structured response: {e}")
    
    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """Stream responses from GPT."""
        messages = self._prepare_messages(prompt, system_prompt)
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": True,
            **self.config.extra_params,
            **kwargs
        }
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                self.API_URL,
                headers=self._get_headers(),
                json=payload,
                timeout=self.config.timeout
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0]["delta"]
                            if "content" in delta:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue