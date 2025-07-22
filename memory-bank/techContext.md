# Technical Context: Front Office Analytics AI Platform

## Technology Stack

### Frontend
- **Framework**: React 18+ with TypeScript 5+
- **State Management**: Redux Toolkit + RTK Query
- **UI Components**: Material-UI v5 or Ant Design
- **Build Tool**: Vite
- **Testing**: Jest + React Testing Library
- **Storybook**: For component development
- **Code Quality**: ESLint + Prettier

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Package Manager**: uv (not pip/poetry)
- **ORM**: SQLAlchemy 2.0+
- **Data Validation**: Pydantic v2
- **Testing**: pytest + pytest-asyncio
- **Code Quality**: Ruff (linting + formatting)

### AI/ML Stack
- **LLM Provider**: Anthropic Claude API
- **Embeddings**: OpenAI Ada or Sentence Transformers
- **Vector Store**: Pinecone or Weaviate
- **ML Framework**: scikit-learn for metrics
- **Document Processing**: PyPDF2, pdfplumber

### Data Layer
- **Primary Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Message Queue**: RabbitMQ
- **Search**: Elasticsearch 8+
- **Object Storage**: AWS S3 or MinIO

### Infrastructure
- **Container**: Docker + Docker Compose
- **Orchestration**: Kubernetes (EKS/GKE)
- **Cloud Provider**: AWS (primary), Azure/GCP (multi-cloud)
- **IaC**: Terraform
- **CI/CD**: GitHub Actions

### Monitoring & Observability
- **Metrics**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: OpenTelemetry + Jaeger
- **Error Tracking**: Sentry
- **Alerting**: PagerDuty

## Development Setup

### Prerequisites
```bash
# Required tools
- Python 3.11+
- Node.js 18+ 
- Docker Desktop
- uv (Python package manager)
- git
```

### Local Environment Structure
```
fo-analytics/
├── backend/
│   ├── src/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Core business logic
│   │   ├── services/     # Service layer
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── utils/        # Utilities
│   ├── tests/
│   ├── pyproject.toml    # uv configuration
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── features/     # Feature modules
│   │   ├── hooks/        # Custom hooks
│   │   ├── services/     # API clients
│   │   ├── store/        # Redux store
│   │   └── utils/        # Utilities
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── .github/
    └── workflows/        # CI/CD pipelines
```

## Key Dependencies

### Python Backend
```toml
[project]
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "asyncpg>=0.29.0",
    "redis>=5.0.0",
    "aio-pika>=9.3.0",      # RabbitMQ client
    "httpx>=0.25.0",         # Async HTTP client
    "anthropic>=0.8.0",      # Claude API
    "boto3>=1.34.0",         # AWS SDK
    "python-multipart>=0.0.6",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "alembic>=1.13.0",       # Database migrations
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
    "pre-commit>=3.6.0",
]
```

### Frontend Dependencies
```json
{
  "dependencies": {
    "@reduxjs/toolkit": "^2.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0",
    "@mui/material": "^5.15.0",
    "react-hook-form": "^7.48.0",
    "react-query": "^3.39.0",
    "recharts": "^2.10.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "@storybook/react-vite": "^7.6.0",
    "vitest": "^1.1.0",
    "eslint": "^8.56.0",
    "prettier": "^3.1.0"
  }
}
```

## Development Tools Configuration

### Python (pyproject.toml)
```toml
[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W", "B", "Q"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
asyncio_mode = "auto"

[tool.mypy]
python_version = "3.11"
strict = true
```

### TypeScript (tsconfig.json)
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "lib": ["ES2020", "DOM"],
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

## API Design Standards

### RESTful Endpoints
```
GET    /api/v1/documents          # List documents
POST   /api/v1/documents          # Upload document
GET    /api/v1/documents/{id}     # Get document
DELETE /api/v1/documents/{id}     # Delete document

POST   /api/v1/strategies/extract # Extract strategies
GET    /api/v1/strategies         # List strategies
GET    /api/v1/strategies/{id}    # Get strategy

POST   /api/v1/backtests          # Create backtest
GET    /api/v1/backtests/{id}     # Get backtest results
```

### Response Format
```python
class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[ErrorDetail] = None
    metadata: Optional[Dict] = None
```

## Security Considerations

### Authentication
- JWT tokens with refresh mechanism
- SAML 2.0 for enterprise SSO
- API keys for service accounts
- Session timeout: 8 hours

### API Security
- Rate limiting: 100 req/min per user
- Request size limit: 100MB (documents)
- CORS configuration for frontend
- Input validation on all endpoints

### Data Protection
- Encryption at rest (AES-256)
- TLS 1.3 for all communications
- Sensitive data masking in logs
- Regular security scanning

## Performance Requirements

### API Response Times
- p50: <100ms
- p95: <500ms
- p99: <1000ms

### Processing Targets
- Document upload: <10 seconds
- Strategy extraction: <5 minutes
- Backtest execution: <30 seconds per year of data

### Scalability
- Support 1000+ concurrent users
- Process 10+ documents simultaneously
- Handle 100GB+ document storage
- Scale horizontally with Kubernetes

## Integration Patterns

### LLM Integration
```python
# Anthropic Claude configuration
CLAUDE_MODEL = "claude-3-opus-20240229"
MAX_TOKENS = 4096
TEMPERATURE = 0.2  # Lower for consistency

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # Exponential backoff
```

### External Services
- **AWS S3**: Document storage
- **SendGrid**: Email notifications
- **Stripe**: Payment processing
- **Auth0/Okta**: SSO integration

## Testing Strategy

### Backend Testing
- Unit tests: 90%+ coverage
- Integration tests: API endpoints
- Performance tests: Load testing
- Security tests: OWASP compliance

### Frontend Testing
- Component tests: React Testing Library
- Integration tests: API mocking
- E2E tests: Playwright
- Visual tests: Storybook

## Deployment Pipeline

### CI/CD Workflow
1. Code push triggers GitHub Actions
2. Run linting and type checking
3. Execute test suite
4. Build Docker images
5. Push to registry
6. Deploy to staging
7. Run smoke tests
8. Manual approval for production
9. Blue-green deployment
10. Post-deployment monitoring