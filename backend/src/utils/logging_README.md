# Structured Logging Implementation

This document describes the structured logging system implemented for the FO Analytics platform.

## Overview

The logging system provides:
- **JSON formatted logs** for production (easy parsing by log aggregation tools)
- **Colored console logs** for development (human-readable)
- **Request ID context** for distributed tracing
- **Performance logging** for API endpoints and operations
- **Automatic log level management** based on environment
- **Sensitive data censoring** to prevent credential leakage

## Components

### 1. Logging Configuration (`src/utils/logging.py`)

The main logging configuration module that sets up structured logging using `structlog`.

#### Key Features:
- Environment-based configuration (development vs production)
- Automatic timestamp and application context addition
- Sensitive data censoring (passwords, tokens, API keys)
- Request/correlation ID support for tracing

#### Basic Usage:
```python
from src.utils.logging import logger, configure_logging

# Initialize logging (done automatically in main.py)
configure_logging()

# Basic logging
logger.info("user_registered", user_id="123", email="user@example.com")
logger.warning("rate_limit_approaching", current=95, limit=100)
logger.error("database_connection_failed", host="db.example.com", exc_info=True)
```

### 2. Request Logging Middleware (`src/middleware/logging.py`)

Middleware that automatically logs all HTTP requests and responses.

#### Features:
- Generates unique request IDs for each request
- Logs request method, path, headers, and query parameters
- Logs response status codes and duration
- Adds request ID to response headers
- Filters sensitive headers before logging

#### Configuration:
```python
from src.middleware.logging import RequestLoggingMiddleware

app.add_middleware(
    RequestLoggingMiddleware,
    skip_paths={"/health", "/metrics"},  # Paths to skip logging
    log_request_body=False,              # Don't log request bodies by default
    log_response_body=False,             # Don't log response bodies by default
)
```

### 3. Performance Logging Middleware (`src/middleware/logging.py`)

Specialized middleware for tracking request performance.

#### Features:
- Tracks request duration
- Logs slow requests (configurable threshold)
- Adds response time headers
- Integrates with the performance logging system

#### Configuration:
```python
from src.middleware.logging import PerformanceLoggingMiddleware

app.add_middleware(
    PerformanceLoggingMiddleware,
    slow_request_threshold_ms=500.0,  # Log requests slower than 500ms
)
```

## Usage Patterns

### 1. Basic Logging in API Endpoints

```python
from src.utils.logging import logger, set_user_context

@router.post("/login")
async def login(login_data: UserLogin):
    logger.info("login_attempt", email=login_data.email)
    
    try:
        user, tokens = await auth_service.login(login_data)
        
        # Set user context for subsequent logs
        set_user_context(user_id=str(user.id), username=user.email)
        
        logger.info("login_successful", user_id=str(user.id), role=user.role.value)
        return tokens
        
    except ValueError as e:
        logger.warning("login_failed", email=login_data.email, reason=str(e))
        raise HTTPException(status_code=401, detail=str(e))
```

### 2. Performance Logging

```python
from src.utils.logging import logger, LoggerAdapter

async def process_document(document_id: str):
    log_adapter = LoggerAdapter(logger)
    
    # Track overall operation performance
    with log_adapter.performance("document_processing"):
        # Track sub-operations
        with log_adapter.performance("pdf_parsing"):
            content = await parse_pdf(document_id)
        
        with log_adapter.performance("strategy_extraction"):
            strategies = await extract_strategies(content)
        
        logger.info(
            "document_processed",
            document_id=document_id,
            strategies_found=len(strategies)
        )
```

### 3. Structured Data Logging

```python
# Log complex objects and metrics
backtest_results = {
    "strategy_id": "strat_123",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "metrics": {
        "total_return": 0.15,
        "sharpe_ratio": 1.2,
        "max_drawdown": -0.08
    },
    "trades": 150
}

logger.info("backtest_completed", **backtest_results)
```

### 4. Error Logging with Context

```python
try:
    result = await external_api_call()
except httpx.HTTPError as e:
    logger.error(
        "external_api_failed",
        service="anthropic",
        endpoint="/v1/messages",
        status_code=getattr(e.response, 'status_code', None),
        error_message=str(e),
        retry_count=current_retry,
        exc_info=True  # Include full traceback
    )
```

### 5. Correlation ID for Distributed Tracing

```python
from src.utils.logging import set_correlation_id

async def process_user_request(request_data):
    # Set correlation ID for the entire operation
    correlation_id = f"req_{uuid.uuid4()}"
    set_correlation_id(correlation_id)
    
    # All subsequent logs will include this correlation ID
    logger.info("request_processing_started", operation="document_upload")
    
    # ... process request ...
    
    logger.info("request_processing_completed", duration_ms=1500)
```

## Log Output Examples

### Development Mode (debug=True)
Colored, human-readable format:
```
2025-01-15T10:30:45.123456+00:00 | INFO | login_attempt | app_name='FO Analytics' email='user@example.com' request_id='req_123' | auth.py:75
```

### Production Mode (debug=False)
JSON format for log aggregation:
```json
{
  "timestamp": "2025-01-15T10:30:45.123456+00:00",
  "level": "INFO",
  "event": "login_attempt",
  "app_name": "FO Analytics",
  "app_version": "0.1.0",
  "environment": "production",
  "email": "user@example.com",
  "request_id": "req_123"
}
```

## Configuration Options

The logging system automatically configures based on environment variables:

- `DEBUG=true`: Enables debug mode with colored console output
- `DEBUG=false` or unset: Enables production mode with JSON output

Additional configuration through `src/core/config.py`:
- `app_name`: Application name added to all logs
- `app_version`: Application version added to all logs

## Security Features

### Automatic Data Censoring
The following fields are automatically redacted in logs:
- `password`
- `token`
- `secret`
- `api_key`
- `authorization`
- `cookie`

### Safe Header Logging
HTTP headers are filtered to remove sensitive authentication information before logging.

## Integration with Monitoring Tools

The JSON output format is designed to work seamlessly with:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Fluentd**
- **Datadog**
- **CloudWatch Logs**
- **Google Cloud Logging**

Example Elasticsearch query for finding failed login attempts:
```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"event": "login_failed"}},
        {"range": {"timestamp": {"gte": "now-1h"}}}
      ]
    }
  }
}
```

## Best Practices

### 1. Use Structured Logging
✅ **Good:**
```python
logger.info("user_action", user_id="123", action="document_upload", file_size_mb=25.3)
```

❌ **Bad:**
```python
logger.info(f"User {user_id} uploaded document of size {file_size}MB")
```

### 2. Include Relevant Context
✅ **Good:**
```python
logger.error("payment_failed", user_id="123", amount=99.99, currency="USD", payment_method="stripe")
```

❌ **Bad:**
```python
logger.error("Payment failed")
```

### 3. Use Appropriate Log Levels
- `DEBUG`: Detailed diagnostic information
- `INFO`: General operational information
- `WARNING`: Something unexpected happened but system continues
- `ERROR`: Serious problem occurred
- `CRITICAL`: System may be unable to continue

### 4. Performance Logging
Always wrap expensive operations:
```python
with log_adapter.performance("database_query"):
    results = await db.execute(complex_query)
```

### 5. Exception Logging
Always include `exc_info=True` for exceptions:
```python
except Exception as e:
    logger.error("operation_failed", operation="user_registration", exc_info=True)
```

## Testing

The logging system includes comprehensive tests in `tests/unit/test_logging.py`. Run tests with:

```bash
PYTHONPATH=/path/to/backend uv run pytest tests/unit/test_logging.py -v
```

## Troubleshooting

### Issue: Logs not appearing
**Solution:** Ensure `configure_logging()` is called before using the logger.

### Issue: Sensitive data in logs
**Solution:** The censoring system should catch common patterns, but add custom fields to the `sensitive_keys` set in `censor_sensitive_data()`.

### Issue: Poor performance
**Solution:** Avoid logging large objects. Use sampling for high-frequency events.

### Issue: Context not preserved
**Solution:** Ensure middleware is properly configured and context is set at the beginning of request processing.

## Future Enhancements

- [ ] Add support for structured error codes
- [ ] Implement log sampling for high-traffic endpoints
- [ ] Add distributed tracing integration (OpenTelemetry)
- [ ] Implement log-based alerting triggers
- [ ] Add support for custom log processors