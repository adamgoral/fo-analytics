# System Patterns: Front Office Analytics AI Platform

## Architecture Overview

### System Design: Microservices Architecture
The platform follows a microservices architecture pattern with clear service boundaries and asynchronous communication.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Web Client    │────▶│   API Gateway   │────▶│  Auth Service   │
│  (React/TS)     │     │   (Kong/Nginx)  │     │    (FastAPI)    │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │   Document   │ │      AI      │ │  Backtesting │
            │   Service    │ │   Service    │ │   Service    │
            │  (FastAPI)   │ │  (FastAPI)   │ │  (FastAPI)   │
            └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
                   │                │                │
                   └────────────────┴────────────────┘
                                   │
                           ┌───────▼────────┐
                           │   Message Bus  │
                           │  (RabbitMQ)    │
                           └───────┬────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │  PostgreSQL  │ │    Redis     │ │Elasticsearch │
            │  (Primary)   │ │   (Cache)    │ │   (Search)   │
            └──────────────┘ └──────────────┘ └──────────────┘
```

## Key Design Patterns

### 1. Event-Driven Architecture
- **Pattern**: Publish-Subscribe via RabbitMQ
- **Use Cases**: 
  - Document processing pipeline
  - Strategy extraction workflow
  - Backtest job orchestration
- **Benefits**: Loose coupling, scalability, fault tolerance
- **Implementation Status**: ✅ RabbitMQ configured in Docker, ready for use

### 2. API Gateway Pattern
- **Implementation**: Kong or Nginx
- **Responsibilities**:
  - Request routing
  - Authentication/authorization
  - Rate limiting
  - Request/response transformation
  - SSL termination

### 3. Repository Pattern (✅ Implemented July 22, 2025)
- **Purpose**: Abstract data access logic
- **Implementation Status**: Fully implemented with async support
- **Benefits**:
  - Clean separation between business logic and data access
  - Easy to mock for testing
  - Consistent API across all entities
  - Type-safe with generics
- **Structure**:
  - **BaseRepository**: Generic CRUD operations with type safety
  - **Specialized Repositories**: User, Document, Strategy, Backtest
  - **Unit of Work**: Transaction management across repositories
  - **Dependency Injection**: FastAPI integration ready
  
  ```python
  # Base repository with generics
  class BaseRepository(Generic[ModelType]):
      async def get(self, id: UUID) -> Optional[ModelType]
      async def get_all(self, skip: int, limit: int) -> List[ModelType]
      async def create(self, **kwargs) -> ModelType
      async def update(self, id: UUID, **kwargs) -> Optional[ModelType]
      async def delete(self, id: UUID) -> bool
      async def exists(self, id: UUID) -> bool
  
  # Unit of Work pattern for transactions
  async with UnitOfWork() as uow:
      user = await uow.users.create(...)
      document = await uow.documents.create(user_id=user.id, ...)
      await uow.commit()
  
  # FastAPI dependency injection
  async def get_user(
      user_id: UUID,
      repo: UserRepository = Depends(get_user_repository)
  ):
      return await repo.get(user_id)
  ```

### 4. Domain-Driven Design (DDD)
- **Bounded Contexts**:
  - Document Management
  - Strategy Extraction
  - Backtesting
  - User Management
- **Aggregates**: Strategy, Document, Backtest, User
- **Value Objects**: TradingSignal, PerformanceMetrics

### 5. CQRS Pattern
- **Commands**: Write operations through message bus
- **Queries**: Read operations with caching
- **Benefits**: Optimized read/write paths, scalability

## Service Responsibilities

### Document Service
- **Primary Responsibility**: PDF storage and retrieval
- **Key Patterns**:
  - Facade pattern for storage abstraction
  - Strategy pattern for different file processors
  - Chain of responsibility for validation pipeline

### AI Service
- **Primary Responsibility**: LLM integration and strategy extraction
- **Key Patterns**:
  - Adapter pattern for LLM providers
  - Circuit breaker for API resilience
  - Retry pattern with exponential backoff
  - Template method for extraction workflows

### Backtesting Service
- **Primary Responsibility**: Strategy execution and performance analysis
- **Key Patterns**:
  - Strategy pattern for different frameworks
  - Factory pattern for backtest creation
  - Observer pattern for progress updates
  - Decorator pattern for metric calculations

## Data Flow Patterns

### Document Processing Pipeline
```
1. Upload → Document Service
2. Validate → Store in S3
3. Publish "DocumentUploaded" event
4. AI Service consumes event
5. Extract strategies → Store results
6. Publish "StrategiesExtracted" event
7. Notify user via WebSocket
```

### Strategy Backtesting Flow
```
1. User requests backtest
2. API Gateway → Backtesting Service
3. Validate parameters
4. Publish "BacktestRequested" event
5. Worker picks up job
6. Execute backtest
7. Calculate metrics
8. Store results
9. Publish "BacktestCompleted" event
10. Update UI via WebSocket
```

## Integration Patterns

### LLM Integration
- **Pattern**: Adapter with Circuit Breaker
- **Implementation**:
  ```python
  class LLMAdapter(ABC):
      @abstractmethod
      async def extract_strategies(self, content: str) -> List[Strategy]
  
  class ClaudeAdapter(LLMAdapter):
      @circuit_breaker(failure_threshold=5)
      async def extract_strategies(self, content: str) -> List[Strategy]
  ```

### External API Integration
- **Pattern**: Gateway with Retry
- **Key Considerations**:
  - Rate limiting respect
  - Timeout configuration
  - Error handling and fallbacks
  - Response caching

## Security Patterns

### Authentication & Authorization
- **Pattern**: Token-based with SAML SSO
- **Implementation**:
  - JWT for API authentication
  - SAML for enterprise SSO
  - RBAC for authorization
  - API key for service-to-service

### Data Security
- **Encryption at Rest**: AES-256 for sensitive data
- **Encryption in Transit**: TLS 1.3
- **Key Management**: AWS KMS or HashiCorp Vault
- **Audit Logging**: All data access logged

## Performance Patterns

### Caching Strategy
- **L1 Cache**: Application-level (in-memory)
- **L2 Cache**: Redis for distributed caching
- **Cache Patterns**:
  - Cache-aside for user data
  - Write-through for strategy results
  - TTL-based expiration

### Database Optimization
- **Read Replicas**: For query scaling
- **Connection Pooling**: PgBouncer
- **Query Optimization**: Indexed lookups
- **Partitioning**: Time-based for historical data

## Error Handling Patterns

### Resilience Patterns
1. **Circuit Breaker**: Prevent cascade failures
2. **Retry with Backoff**: Handle transient failures
3. **Timeout**: Prevent hanging requests
4. **Bulkhead**: Isolate critical resources
5. **Fallback**: Graceful degradation

### Error Response Structure
```python
class ErrorResponse(BaseModel):
    error_id: UUID
    error_code: str
    message: str
    details: Optional[Dict]
    timestamp: datetime
    correlation_id: UUID
```

## Monitoring Patterns

### Observability Stack
- **Metrics**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: OpenTelemetry + Jaeger
- **Alerting**: PagerDuty integration

### Key Metrics
- **Business**: Strategies extracted/hour, backtests completed
- **Technical**: API latency, error rates, queue depth
- **Resource**: CPU, memory, disk usage

## Deployment Patterns

### Container Orchestration
- **Platform**: Kubernetes
- **Patterns**:
  - Rolling updates
  - Blue-green deployments
  - Canary releases
  - Health checks and readiness probes

### Infrastructure as Code
- **Tool**: Terraform
- **Patterns**:
  - Modular configuration
  - Environment-specific variables
  - State management
  - Automated provisioning