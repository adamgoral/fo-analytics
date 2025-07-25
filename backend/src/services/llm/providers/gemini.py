"""Google Gemini LLM provider implementation."""

import json
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel

from ..base import LLMConfig, LLMProvider, LLMProviderType, LLMResponse


class GeminiProvider(LLMProvider):
    """Google Gemini API provider."""
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    
    def _validate_config(self) -> None:
        """Validate Gemini-specific configuration."""
        if not self.config.api_key:
            raise ValueError("Google API key is required")
        
        valid_models = [
            "gemini-1.5-pro",
            "gemini-1.5-pro-latest",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-1.0-pro",
            "gemini-pro",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash-latest",
        ]
        
        if self.config.model not in valid_models:
            raise ValueError(
                f"Invalid Gemini model: {self.config.model}. "
                f"Valid models: {', '.join(valid_models)}"
            )
    
    def _get_url(self, endpoint: str) -> str:
        """Get the full URL for a Gemini API endpoint."""
        return f"{self.BASE_URL}/{self.config.model}:{endpoint}?key={self.config.api_key}"
    
    def _convert_messages_to_gemini_format(
        self,
        messages: list[Dict[str, str]]
    ) -> tuple[Optional[str], list[Dict[str, Any]]]:
        """Convert standard messages to Gemini format.
        
        Returns:
            Tuple of (system_instruction, contents)
        """
        system_instruction = None
        contents = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            elif msg["role"] == "user":
                contents.append({
                    "role": "user",
                    "parts": [{"text": msg["content"]}]
                })
            elif msg["role"] == "assistant":
                contents.append({
                    "role": "model",
                    "parts": [{"text": msg["content"]}]
                })
        
        return system_instruction, contents
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from Gemini."""
        messages = self._prepare_messages(prompt, system_prompt)
        system_instruction, contents = self._convert_messages_to_gemini_format(messages)
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_tokens,
                **self.config.extra_params,
                **kwargs
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._get_url("generateContent"),
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
        
        # Extract response
        candidate = data["candidates"][0]
        content = candidate["content"]["parts"][0]["text"]
        
        # Calculate token usage (Gemini provides this differently)
        usage_metadata = data.get("usageMetadata", {})
        
        return LLMResponse(
            content=content,
            model=self.config.model,
            provider=LLMProviderType.GEMINI,
            usage={
                "input_tokens": usage_metadata.get("promptTokenCount", 0),
                "output_tokens": usage_metadata.get("candidatesTokenCount", 0),
                "total_tokens": usage_metadata.get("totalTokenCount", 0)
            },
            raw_response=data,
            metadata={
                "finish_reason": candidate.get("finishReason"),
                "safety_ratings": candidate.get("safetyRatings", [])
            }
        )
    
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[BaseModel],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> tuple[BaseModel, LLMResponse]:
        """Generate a structured response using Gemini."""
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
        
        # Add response MIME type for JSON
        extra_kwargs = kwargs.copy()
        extra_kwargs["responseMimeType"] = "application/json"
        
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
        """Stream responses from Gemini."""
        messages = self._prepare_messages(prompt, system_prompt)
        system_instruction, contents = self._convert_messages_to_gemini_format(messages)
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_tokens,
                **self.config.extra_params,
                **kwargs
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        
        async with httpx.AsyncClient() as client:
            # Gemini uses streamGenerateContent endpoint for streaming
            async with client.stream(
                "POST",
                self._get_url("streamGenerateContent") + "&alt=sse",
                json=payload,
                timeout=self.config.timeout
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        
                        try:
                            data = json.loads(data_str)
                            if "candidates" in data and data["candidates"]:
                                candidate = data["candidates"][0]
                                if "content" in candidate and "parts" in candidate["content"]:
                                    for part in candidate["content"]["parts"]:
                                        if "text" in part:
                                            yield part["text"]
                        except json.JSONDecodeError:
                            continue