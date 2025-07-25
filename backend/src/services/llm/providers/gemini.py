"""Google Gemini LLM provider implementation."""

import json
import logging
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel

from ..base import LLMConfig, LLMProvider, LLMProviderType, LLMResponse

logger = logging.getLogger(__name__)


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
                "maxOutputTokens": kwargs.get('max_tokens', self.config.max_tokens),
                **{k: v for k, v in self.config.extra_params.items() if k not in kwargs},
                **{k: v for k, v in kwargs.items() if k != 'max_tokens'}
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        
        # Debug logging
        logger.info(f"Gemini streaming request URL: {self._get_url('streamGenerateContent')}")
        logger.info(f"Gemini streaming request payload: {json.dumps(payload, indent=2)}")
        
        try:
            async with httpx.AsyncClient() as client:
                # Use a proper streaming request
                async with client.stream(
                    "POST",
                    self._get_url("streamGenerateContent"),
                    json=payload,
                    timeout=self.config.timeout
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"Gemini API error: {response.status_code} - {error_text.decode()}")
                        response.raise_for_status()
                    
                    # Process the streaming response
                    # Gemini returns JSON objects separated by ",\n"
                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        
                        # Try to find complete JSON objects
                        while True:
                            # Remove leading whitespace and commas
                            buffer = buffer.lstrip(' ,\n\r')
                            if not buffer:
                                break
                                
                            # Try to find a complete JSON object
                            brace_count = 0
                            in_string = False
                            escape_next = False
                            json_end = -1
                            
                            for i, char in enumerate(buffer):
                                if escape_next:
                                    escape_next = False
                                    continue
                                    
                                if char == '\\':
                                    escape_next = True
                                    continue
                                    
                                if char == '"' and not escape_next:
                                    in_string = not in_string
                                    continue
                                    
                                if not in_string:
                                    if char == '{':
                                        brace_count += 1
                                    elif char == '}':
                                        brace_count -= 1
                                        if brace_count == 0:
                                            json_end = i + 1
                                            break
                            
                            if json_end == -1:
                                # No complete JSON object found
                                break
                                
                            # Extract and parse the JSON object
                            json_str = buffer[:json_end]
                            buffer = buffer[json_end:]
                            
                            try:
                                data = json.loads(json_str)
                                if "candidates" in data and data["candidates"]:
                                    candidate = data["candidates"][0]
                                    if "content" in candidate and "parts" in candidate["content"]:
                                        for part in candidate["content"]["parts"]:
                                            if "text" in part:
                                                yield part["text"]
                            except json.JSONDecodeError as e:
                                logger.debug(f"Failed to parse JSON object: {json_str[:100]}..., error: {e}")
                                continue
        except Exception as e:
            logger.error(f"Error in Gemini streaming: {str(e)}")
            raise