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

### 1. Event-Driven Architecture (✅ Implemented July 23, 2025)
- **Pattern**: Publish-Subscribe via RabbitMQ
- **Implementation Status**: ✅ Fully operational with aio-pika
- **Use Cases**: 
  - Document processing pipeline (✅ Implemented)
  - Strategy extraction workflow (✅ Implemented)
  - Backtest job orchestration (Planned)
- **Benefits**: 
  - Loose coupling between services
  - Horizontal scalability for workers
  - Fault tolerance with retry and DLQ
  - Asynchronous processing for long operations
- **Architecture**:
  ```python
  # Message flow
  Upload → Publish → Queue → Worker → Process → Result
                       ↓
                  Dead Letter Queue (on failure)
  
  # Configuration
  Exchange: fo_analytics (topic)
  Main Queue: document_processing
  DLQ: document_processing_dlq
  Max Retries: 3 with exponential backoff
  ```

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

### 6. Service Layer Pattern (✅ Implemented July 22, 2025)
- **Purpose**: Encapsulate business logic
- **Implementation**: Separate service classes for business operations
- **Benefits**:
  - API endpoints remain thin
  - Business logic is testable
  - Reusable across different interfaces
- **Example**:
  ```python
  class AuthService:
      async def register(self, email: str, password: str) -> User
      async def login(self, email: str, password: str) -> TokenPair
      async def refresh_token(self, refresh_token: str) -> TokenPair
  ```

### 7. Structured Logging Pattern (✅ Implemented July 22, 2025)
- **Library**: structlog for JSON structured logs
- **Features**:
  - Environment-based formatting (JSON/colored)
  - Request tracing with correlation IDs
  - Performance monitoring built-in
  - Sensitive data automatic censoring
- **Integration**:
  - Middleware for request/response logging
  - Context propagation throughout request
  - User context for audit trails

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

### Document Service (✅ Storage & Parsing Implemented July 23, 2025)
- **Primary Responsibility**: Document storage, retrieval, and processing
- **Implemented Components**:
  - ✅ MinIO/S3 storage service with aioboto3
  - ✅ User-isolated storage structure (user_id/unique_key.ext)
  - ✅ Streaming download with presigned URLs
  - ✅ Automatic bucket creation and management
  - ✅ Comprehensive error handling and cleanup
  - ✅ LlamaIndex-based document parsing service
  - ✅ PyMuPDFReader for advanced PDF processing
  - ✅ Support for PDF, TXT, and Markdown formats
  - ✅ Page-by-page parsing capability
  - ✅ Metadata extraction from documents
- **Key Patterns**:
  - **Storage Abstraction**: StorageService wraps S3 operations
  - **Factory Pattern**: Configurable storage backends (MinIO/S3/Azure)
  - **Repository Pattern**: Document metadata in PostgreSQL
  - **Adapter Pattern**: LlamaIndex adapters for different file types
  - **Strategy Pattern**: Different parsing strategies per document type
  - **Strategy Pattern**: Different file processors (PDF, DOC, TXT)
  - **Chain of Responsibility**: Validation pipeline
- **Storage Architecture**:
  ```python
  # Storage service interface
  class StorageService:
      async def upload_file(file_content, file_name, user_id) -> str
      async def download_file(file_key) -> (bytes, metadata)
      async def delete_file(file_key) -> bool
      async def generate_presigned_url(file_key) -> str
      async def list_user_files(user_id) -> List[dict]
  
  # Document flow
  Upload → Validate → Store in MinIO → Save metadata → Return key
  Download → Verify ownership → Generate URL/Stream → Return content
  ```

### AI Service (✅ LLM Provider Integration Implemented July 23, 2025)
- **Primary Responsibility**: LLM integration and strategy extraction
- **Implemented Components**:
  - ✅ Provider pattern with abstract base class
  - ✅ AnthropicProvider for Claude API integration
  - ✅ Factory pattern for dynamic provider selection
  - ✅ LLMService as unified interface
  - ✅ Retry logic with exponential backoff
  - ✅ Custom exception hierarchy
  - ✅ JSON mode for structured output
  - ✅ Comprehensive test coverage
- **Key Patterns**:
  - **Adapter Pattern**: Each LLM provider (Anthropic, OpenAI, Gemini) implements common interface
  - **Factory Pattern**: `LLMProviderFactory.create()` selects provider based on config
  - **Strategy Pattern**: Different extraction strategies per document type
  - **Circuit Breaker**: Built into retry logic for API resilience
  - **Template Method**: Base extraction workflow with provider-specific implementations
- **Architecture**:
  ```python
  # Provider interface
  class BaseLLMProvider(ABC):
      async def extract_strategies(content: str) -> List[Strategy]
      async def analyze_document(content: str) -> DocumentAnalysis
  
  # Factory pattern
  provider = LLMProviderFactory.create("anthropic")
  
  # Service layer
  llm_service = LLMService(provider)
  strategies = await llm_service.extract_strategies(document_text)
  ```

### Backtesting Service (✅ Advanced Features Implemented July 24, 2025)
- **Primary Responsibility**: Strategy execution and performance analysis
- **Implemented Components**:
  - ✅ Basic backtesting with 5 strategy types (SMA, RSI, Bollinger, Momentum, Custom)
  - ✅ Data loader with yfinance integration for all asset classes
  - ✅ Async execution with thread pool
  - ✅ RabbitMQ integration for job processing
  - ✅ **Portfolio Optimization Module**:
    - Markowitz mean-variance optimization
    - Black-Litterman model implementation
    - Risk parity portfolios
    - Maximum Sharpe/minimum volatility portfolios
    - Efficient frontier generation
  - ✅ **Multi-Strategy Backtesting**:
    - Run multiple strategies simultaneously
    - Portfolio rebalancing (daily/weekly/monthly/quarterly/yearly)
    - Strategy signal combination
    - Integration with all optimization methods
  - ✅ **Advanced Risk Metrics**:
    - Value at Risk (Historical, Parametric, Cornish-Fisher, Monte Carlo)
    - Conditional VaR (CVaR/Expected Shortfall)
    - Comprehensive drawdown analysis
    - Advanced ratios (Omega, Information, Calmar, Sterling, Burke)
    - Relative metrics (Beta, Alpha, Correlation)
- **Key Patterns**:
  - **Strategy Pattern**: Different trading strategies implement common interface
  - **Factory Pattern**: Strategy and optimizer creation
  - **Observer Pattern**: Progress updates via WebSocket
  - **Decorator Pattern**: Risk metric calculations wrap basic results
  - **Composite Pattern**: Multi-strategy portfolios combine individual strategies
- **Architecture**:
  ```python
  # Portfolio optimization
  optimizer = PortfolioOptimizer(returns_data, risk_free_rate=0.02)
  result = optimizer.mean_variance_optimization(target_return=0.10)
  result = optimizer.black_litterman(market_caps, views, confidence)
  
  # Multi-strategy backtesting
  backtester = MultiStrategyBacktester()
  results = await backtester.run_multi_strategy_backtest(
      strategies=[strategy1_config, strategy2_config],
      optimization_method="risk_parity",
      rebalance_frequency="monthly"
  )
  
  # Risk metrics calculation
  calculator = RiskMetricsCalculator(returns, benchmark_returns)
  metrics = calculator.calculate_all_metrics(confidence_levels=[0.95, 0.99])
  ```

## Portfolio Optimization Patterns (✅ Implemented July 24, 2025)

### Optimization Algorithms
- **Markowitz Mean-Variance**: Classic portfolio theory implementation
  - Minimize risk for target return
  - Maximize Sharpe ratio
  - Efficient frontier generation
- **Black-Litterman Model**: Combines market equilibrium with investor views
  - Market capitalization weights as prior
  - Investor views with confidence levels
  - Posterior return estimation
- **Risk Parity**: Equal risk contribution from each asset
  - Iterative optimization for risk balance
  - Suitable for diversified portfolios
- **Numerical Optimization**: Scipy integration
  - SLSQP solver for constrained optimization
  - Custom constraints support
  - Bounds handling for long-only portfolios

### Multi-Strategy Architecture
```python
# Strategy composition pattern
class MultiStrategyPortfolio(Strategy):
    def add_strategy(strategy: BaseStrategy, weight: float)
    def set_optimization_method(method: str, params: dict)
    def _rebalance_portfolio()  # Dynamic weight adjustment
    def _combine_signals(signals: List[float]) -> float
    
# Rebalancing logic
if should_rebalance(current_date):
    returns = get_strategy_returns(lookback_days)
    optimizer = PortfolioOptimizer(returns)
    weights = optimizer.optimize()
    apply_weights(weights)
```

### Risk Metrics Framework
- **Value at Risk (VaR)**:
  - Historical: Empirical percentile
  - Parametric: Normal distribution assumption
  - Cornish-Fisher: Adjusts for skewness/kurtosis
  - Monte Carlo: Simulation-based
- **Performance Metrics**:
  - Sharpe, Sortino, Calmar ratios
  - Information ratio for benchmark comparison
  - Omega ratio for gain/loss asymmetry
- **Drawdown Analysis**:
  - Maximum drawdown tracking
  - Recovery time analysis
  - Drawdown duration statistics

### API Integration
- **Portfolio Endpoints**:
  - POST /portfolio/optimize - Run optimization
  - POST /portfolio/efficient-frontier - Generate frontier
  - POST /portfolio/multi-strategy-backtest - Multi-strategy test
  - POST /portfolio/risk-metrics - Calculate risk metrics
- **Async Processing**: Thread pool for CPU-intensive calculations
- **Result Caching**: Redis for expensive computations (planned)

## Data Flow Patterns

### Document Processing Pipeline (✅ Implemented July 23, 2025)
```
1. Upload → Document Service API
2. Validate → Store in MinIO/S3
3. Publish DocumentProcessingMessage to RabbitMQ
4. Worker consumes message from queue
5. Parse document with LlamaIndex
6. Extract strategies with Claude API
7. Store results in PostgreSQL
8. Update document status
9. Publish ProcessingResultMessage
10. (Future) Notify user via WebSocket

Current Implementation:
- Async processing with status tracking
- Retry logic for transient failures
- Dead letter queue for permanent failures
- Comprehensive error handling
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

### LLM Integration (✅ Implemented July 23, 2025)
- **Pattern**: Provider Pattern with Factory
- **Implementation Status**: Complete with Anthropic Claude integration
- **Architecture**:
  ```python
  # Base provider interface
  class BaseLLMProvider(ABC):
      @abstractmethod
      async def extract_strategies(self, content: str, options: Optional[Dict] = None) -> Dict[str, Any]
      
      @abstractmethod
      async def analyze_document(self, content: str, analysis_type: str) -> Dict[str, Any]
  
  # Anthropic implementation
  class AnthropicProvider(BaseLLMProvider):
      def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
          self.client = AsyncAnthropic(api_key=api_key)
          self.model = model
      
      @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
      async def extract_strategies(self, content: str, options: Optional[Dict] = None) -> Dict[str, Any]:
          # Implementation with structured JSON output
  
  # Factory pattern
  class LLMProviderFactory:
      @staticmethod
      def create(provider_type: str = "anthropic") -> BaseLLMProvider:
          if provider_type == "anthropic":
              return AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY)
          # Future: OpenAI, Gemini providers
  ```
- **Error Handling**:
  - Custom exceptions: LLMProviderError, RateLimitError, InvalidResponseError
  - Retry logic with exponential backoff
  - Graceful fallbacks for API failures

### External API Integration
- **Pattern**: Gateway with Retry
- **Key Considerations**:
  - Rate limiting respect
  - Timeout configuration
  - Error handling and fallbacks
  - Response caching

## Security Patterns

### Authentication & Authorization ✅ (JWT Implemented July 22, 2025)
- **Pattern**: Token-based with SAML SSO
- **Implementation Status**:
  - ✅ JWT for API authentication (implemented with python-jose)
  - ✅ Access tokens (30min) and refresh tokens (7 days)
  - ✅ RBAC for authorization (admin, analyst, viewer roles)
  - ✅ Password hashing with bcrypt via passlib
  - ✅ Authentication middleware for protected routes
  - ⏳ SAML for enterprise SSO (planned)
  - ⏳ API key for service-to-service (planned)
- **API Endpoints**:
  - POST /api/v1/auth/register - User registration
  - POST /api/v1/auth/login - User login with token generation
  - POST /api/v1/auth/refresh - Refresh access token
  - POST /api/v1/auth/change-password - Change password
  - GET /api/v1/auth/me - Get current user info

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

## Document Processing Patterns (✅ Implemented July 23, 2025)

### Document Parsing Architecture
- **Framework**: LlamaIndex for advanced document understanding
- **PDF Engine**: PyMuPDFReader for superior text extraction
- **Supported Formats**: PDF, TXT, Markdown
- **Key Features**:
  - Preserves document formatting and structure
  - Handles complex layouts and tables
  - Page-by-page parsing capability
  - Automatic metadata extraction
  - Direct LLM integration path

### Processing Pipeline Pattern
```python
# 1. Upload → 2. Store → 3. Parse → 4. Extract → 5. Analyze
document = await upload_document(file)
storage_key = await storage_service.upload_file(document)
parsed_text = await parser_service.parse_document(storage_key)
strategies = await ai_service.extract_strategies(parsed_text)
results = await backtest_service.analyze_strategy(strategies)
```

### Storage Patterns
- **User Isolation**: Files stored as `{user_id}/{unique_key}.{ext}`
- **Temporary Processing**: Use tempfile for parsing operations
- **Cleanup Strategy**: Automatic deletion on errors
- **Streaming**: Large file support via streaming responses

## Message Queue Patterns (✅ Implemented July 23, 2025)

### RabbitMQ Architecture
- **Connection Management**:
  - Robust connection with automatic reconnection
  - Channel pooling for performance
  - Graceful shutdown handling
- **Message Schema**:
  - Pydantic models for type safety
  - JSON serialization for messages
  - Correlation IDs for tracking
- **Queue Configuration**:
  ```python
  # Main processing queue
  document_processing:
    - Durable: true
    - TTL: 1 hour
    - Dead letter exchange: ""
    - Dead letter routing key: document_processing_dlq
  
  # Dead letter queue
  document_processing_dlq:
    - Durable: true
    - TTL: 24 hours
    - Manual intervention required
  ```

### Message Processing Patterns
- **Publisher Pattern**:
  - Fire-and-forget for document upload
  - Correlation ID for request tracking
  - Error handling without blocking API
- **Consumer Pattern**:
  - Acknowledgment after successful processing
  - Retry with exponential backoff
  - Dead letter queue for failed messages
  - Status updates throughout pipeline
- **Worker Scaling**:
  - Multiple workers can consume from same queue
  - Prefetch count = 1 for fair distribution
  - Graceful shutdown on SIGTERM

### Error Recovery Strategy
1. **Transient Failures** (network, rate limits):
   - Retry up to 3 times
   - Exponential backoff: 1s, 2s, 4s
   - Preserve original message
2. **Permanent Failures** (invalid document, parsing error):
   - Send to dead letter queue
   - Log detailed error information
   - Update document status to failed
3. **System Failures** (worker crash):
   - Message remains in queue (not acknowledged)
   - Another worker picks it up
   - At-least-once delivery guarantee

## Error Handling Patterns

### Resilience Patterns
1. **Circuit Breaker**: Prevent cascade failures
2. **Retry with Backoff**: Handle transient failures (✅ Implemented in LLM and Queue)
3. **Timeout**: Prevent hanging requests
4. **Bulkhead**: Isolate critical resources
5. **Fallback**: Graceful degradation

### Error Response Structure (✅ Standardized)
```python
class ErrorResponse(BaseModel):
    error_id: UUID
    error_code: str
    message: str
    details: Optional[Dict]
    timestamp: datetime
    correlation_id: UUID
```

### API Error Handling (✅ Implemented)
- **Consistent Format**: All errors follow same structure
- **HTTP Status Codes**: Proper codes for different errors
- **Validation Errors**: Detailed field-level error messages
- **Business Errors**: Clear messages for domain violations
- **System Errors**: Generic messages with correlation IDs

## Monitoring Patterns

### Observability Stack
- **Metrics**: Prometheus + Grafana
- **Logging**: ✅ Structured JSON logs ready for ELK Stack
- **Tracing**: OpenTelemetry + Jaeger (planned)
- **Alerting**: PagerDuty integration (planned)

### Implemented Logging (✅ July 22, 2025)
- **Structured Format**: JSON logs with consistent schema
- **Request Tracing**: Unique request IDs for correlation
- **Performance Tracking**: Automatic slow request detection
- **Security**: Sensitive data censoring (passwords, tokens, keys)
- **Context Propagation**: User and request context throughout
- **Environment Aware**: JSON for production, colored for development

### Key Metrics
- **Business**: Strategies extracted/hour, backtests completed
- **Technical**: API latency, error rates, queue depth
- **Resource**: CPU, memory, disk usage
- **Security**: Failed auth attempts, permission denials

## Deployment Patterns

### Container Orchestration
- **Platform**: Kubernetes (planned for production)
- **Current**: Docker Compose for development (✅ Implemented)
- **Patterns**:
  - Rolling updates
  - Blue-green deployments
  - Canary releases
  - Health checks and readiness probes

### Development Environment (✅ Implemented)
- **Docker Compose**: Multi-container orchestration
  - PostgreSQL, Redis, RabbitMQ, MinIO services
  - Backend API and Frontend services
  - Document processing worker service
  - All with health checks and proper dependencies
- **Tilt.dev Integration**: Development environment orchestration
  - Live updates without container rebuilds
  - Unified dashboard for all services
  - Integrated development commands
  - Automatic dependency management
  - Worker service with auto-restart
- **Hot Reloading**: Both backend and frontend
- **Health Checks**: All services monitored
- **Networking**: Isolated network with service discovery
- **Volumes**: Persistent data and code mounting
- **Management Tools**:
  - RabbitMQ Management UI: localhost:15672
  - MinIO Console: localhost:9001
  - API Documentation: localhost:8000/api/v1/docs

### CI/CD Pipeline (✅ Implemented)
- **GitHub Actions**: Automated workflows
- **CI Pipeline**: Lint, test, security scan, build
- **CD Pipeline**: Build images, push registry, deploy
- **Security**: Trivy scanning, dependency checks

### Infrastructure as Code
- **Tool**: Terraform (planned for cloud deployment)
- **Patterns**:
  - Modular configuration
  - Environment-specific variables
  - State management
  - Automated provisioning