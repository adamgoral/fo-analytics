# LLM Provider Service

A flexible, provider-agnostic LLM service that supports multiple providers (Anthropic Claude, OpenAI GPT, Google Gemini) for financial strategy extraction.

## Features

- **Multiple Provider Support**: Seamlessly switch between Anthropic Claude, OpenAI GPT, and Google Gemini
- **Unified Interface**: Consistent API across all providers
- **Structured Output**: Support for JSON schema-based structured responses
- **Streaming**: Real-time streaming responses for all providers
- **Configuration-based**: Easy provider switching via environment variables
- **Type-safe**: Full type hints and Pydantic models
- **Async-first**: Built on modern async/await patterns

## Configuration

Set the following environment variables in your `.env` file:

```env
# Choose your provider
LLM_PROVIDER=anthropic  # Options: anthropic, openai, gemini

# Model configuration
LLM_MODEL=claude-3-5-sonnet-20241022  # Model name for the selected provider
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
LLM_TIMEOUT=60

# API Keys (set the one for your chosen provider)
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key
GOOGLE_API_KEY=your-google-api-key
```

## Available Models

### Anthropic Claude
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`
- `claude-3-5-sonnet-20241022`
- `claude-3-5-haiku-20241022`

### OpenAI GPT
- `gpt-4o`
- `gpt-4o-mini`
- `gpt-4-turbo`
- `gpt-4`
- `gpt-3.5-turbo`

### Google Gemini
- `gemini-1.5-pro`
- `gemini-1.5-flash`
- `gemini-1.0-pro`

## Usage Examples

### Basic Usage

```python
from services.llm import LLMService

# Initialize service (uses settings from environment)
llm_service = LLMService()

# Extract strategy from document
result = await llm_service.extract_strategy(document_content)
print(result["strategy_analysis"])
```

### Direct Provider Usage

```python
from services.llm import LLMConfig, LLMProviderFactory, LLMProviderType

# Create a specific provider
config = LLMConfig(
    provider=LLMProviderType.OPENAI,
    api_key="your-api-key",
    model="gpt-4o",
    temperature=0.7,
    max_tokens=2000
)

provider = LLMProviderFactory.create(config)

# Generate response
response = await provider.generate(
    prompt="Analyze this trading strategy...",
    system_prompt="You are a financial analyst..."
)
```

### Structured Output

```python
from pydantic import BaseModel
from services.llm import LLMService

class TradingStrategy(BaseModel):
    name: str
    description: str
    entry_conditions: list[str]
    exit_conditions: list[str]
    risk_level: str
    expected_return: float

llm_service = LLMService()

# Get structured response
strategy, raw_response = await llm_service.provider.generate_structured(
    prompt="Extract the trading strategy from this document...",
    response_model=TradingStrategy
)

print(f"Strategy Name: {strategy.name}")
print(f"Risk Level: {strategy.risk_level}")
```

### Streaming Responses

```python
from services.llm import LLMService

llm_service = LLMService()

# Stream the response
async for chunk in llm_service.provider.stream_generate(
    prompt="Explain this complex trading strategy..."
):
    print(chunk, end="", flush=True)
```

### Switching Providers at Runtime

```python
from services.llm import LLMConfig, LLMProviderType, LLMProviderFactory

# Create different provider configurations
providers = {
    "anthropic": LLMConfig(
        provider=LLMProviderType.ANTHROPIC,
        api_key=settings.anthropic_api_key,
        model="claude-3-5-sonnet-20241022"
    ),
    "openai": LLMConfig(
        provider=LLMProviderType.OPENAI,
        api_key=settings.openai_api_key,
        model="gpt-4o"
    ),
    "gemini": LLMConfig(
        provider=LLMProviderType.GEMINI,
        api_key=settings.google_api_key,
        model="gemini-1.5-pro"
    )
}

# Use different providers for different tasks
for provider_name, config in providers.items():
    provider = LLMProviderFactory.create(config)
    response = await provider.generate("Analyze this document...")
    print(f"{provider_name}: {response.content[:100]}...")
```

## Architecture

The LLM service follows a clean architecture pattern:

```
llm/
├── base.py          # Abstract interfaces and base classes
├── providers/       # Provider implementations
│   ├── anthropic.py
│   ├── openai.py
│   └── gemini.py
├── factory.py       # Factory pattern for provider creation
├── service.py       # High-level service layer
└── README.md       # This file
```

## Error Handling

All providers implement comprehensive error handling:

```python
from services.llm import LLMService

try:
    llm_service = LLMService()
    result = await llm_service.extract_strategy(document)
except ValueError as e:
    # Configuration errors (missing API key, invalid model)
    logger.error(f"Configuration error: {e}")
except httpx.HTTPError as e:
    # API communication errors
    logger.error(f"API error: {e}")
```

## Testing

The service includes comprehensive unit tests with mocked API responses:

```bash
# Run all LLM tests
pytest tests/unit/services/test_llm_providers.py
pytest tests/unit/services/test_llm_service.py
```

## Future Enhancements

- Token usage tracking and cost estimation
- Response caching with Redis
- Rate limiting and retry logic
- Support for additional providers (Cohere, AI21, etc.)
- Fine-tuning support for compatible models
- Prompt template management