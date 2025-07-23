# Message Queue Infrastructure

This module implements the asynchronous message processing system using RabbitMQ.

## Architecture

### Components

1. **Connection Manager** (`connection.py`)
   - Manages RabbitMQ connection lifecycle
   - Implements automatic reconnection
   - Declares exchanges and queues

2. **Message Publisher** (`publisher.py`)
   - Publishes document processing messages
   - Handles retry logic
   - Supports dead letter queue routing

3. **Message Consumer** (`consumer.py`)
   - Processes documents asynchronously
   - Integrates with storage, parser, and LLM services
   - Updates document status in database

4. **Message Schemas** (`schemas.py`)
   - Pydantic models for message validation
   - Type-safe message passing

## Message Flow

```
Document Upload → API → Publisher → RabbitMQ Queue → Consumer → Process → Update DB
                                          ↓
                                    Dead Letter Queue (on failure)
```

## Queue Configuration

- **Exchange**: `fo_analytics` (topic exchange)
- **Main Queue**: `document_processing`
  - Routing key: `document.process`
  - TTL: 1 hour
  - Dead letter routing enabled
- **Dead Letter Queue**: `document_processing_dlq`
  - Routing key: `document.failed`
  - TTL: 24 hours

## Running the Worker

### Docker Compose
```bash
make up  # Starts all services including worker
make worker-logs  # View worker logs
make worker-restart  # Restart worker
```

### Standalone
```bash
cd backend
uv run python -m worker
```

## Error Handling

- Automatic retry with exponential backoff (up to 3 retries)
- Failed messages sent to dead letter queue
- Processing errors logged and stored in database

## Monitoring

Access RabbitMQ Management UI:
- URL: http://localhost:15672
- Username: fo_user
- Password: fo_password

## Testing

Run the pipeline test:
```bash
cd backend
uv run python scripts/test_document_pipeline.py
```

This will:
1. Create a test user
2. Upload a test document
3. Monitor processing status
4. Verify strategy extraction