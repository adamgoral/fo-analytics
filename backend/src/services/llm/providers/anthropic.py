"""Anthropic Claude LLM provider implementation."""

import json
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel

from ..base import LLMConfig, LLMProvider, LLMProviderType, LLMResponse


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""
    
    API_URL = "https://api.anthropic.com/v1/messages"
    
    def _validate_config(self) -> None:
        """Validate Anthropic-specific configuration."""
        if not self.config.api_key:
            raise ValueError("Anthropic API key is required")
        
        valid_models = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
        ]
        
        if self.config.model not in valid_models:
            raise ValueError(
                f"Invalid Anthropic model: {self.config.model}. "
                f"Valid models: {', '.join(valid_models)}"
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers for Anthropic API."""
        return {
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from Claude."""
        messages = self._prepare_messages(prompt, system_prompt)
        
        # Convert to Anthropic format
        anthropic_messages = []
        anthropic_system = None
        
        for msg in messages:
            if msg["role"] == "system":
                anthropic_system = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        payload = {
            "model": self.config.model,
            "messages": anthropic_messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            **self.config.extra_params,
            **kwargs
        }
        
        if anthropic_system:
            payload["system"] = anthropic_system
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.API_URL,
                headers=self._get_headers(),
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
        
        return LLMResponse(
            content=data["content"][0]["text"],
            model=data["model"],
            provider=LLMProviderType.ANTHROPIC,
            usage={
                "input_tokens": data["usage"]["input_tokens"],
                "output_tokens": data["usage"]["output_tokens"],
                "total_tokens": data["usage"]["input_tokens"] + data["usage"]["output_tokens"]
            },
            raw_response=data,
            metadata={
                "stop_reason": data.get("stop_reason"),
                "id": data.get("id")
            }
        )
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[BaseModel],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> tuple[BaseModel, LLMResponse]:
        """Generate a structured response using Claude's JSON mode."""
        # Add JSON schema to the prompt
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
        
        response = await self.generate(
            enhanced_prompt,
            system_prompt=enhanced_system,
            **kwargs
        )
        
        # Parse the JSON response
        try:
            json_content = response.content.strip()
            # Handle code blocks if present
            if json_content.startswith("```json"):
                json_content = json_content[7:]
            if json_content.startswith("```"):
                json_content = json_content[3:]
            if json_content.endswith("```"):
                json_content = json_content[:-3]
            
            parsed_data = json.loads(json_content.strip())
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
        """Stream responses from Claude."""
        messages = self._prepare_messages(prompt, system_prompt)
        
        # Convert to Anthropic format
        anthropic_messages = []
        anthropic_system = None
        
        for msg in messages:
            if msg["role"] == "system":
                anthropic_system = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        payload = {
            "model": self.config.model,
            "messages": anthropic_messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": True,
            **self.config.extra_params,
            **kwargs
        }
        
        if anthropic_system:
            payload["system"] = anthropic_system
        
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
                            if data["type"] == "content_block_delta":
                                yield data["delta"]["text"]
                        except json.JSONDecodeError:
                            continue