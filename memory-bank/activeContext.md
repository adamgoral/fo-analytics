# Active Context: Front Office Analytics AI Platform

## Current State (July 23, 2025)

### Project Phase: Sprint 2 In Progress - Document Processing & AI Integration
The project has completed Sprint 1 with 84% test coverage and is now 75% through Sprint 2. Document processing pipeline with RabbitMQ message queue has been implemented, enabling asynchronous processing of uploaded documents through parsing and AI strategy extraction. WebSocket support has been added for real-time updates.

### Recent Updates (Post-Sprint 1)
- ✅ **Python Import Structure Fixed**: Cleaned up package configuration
  - Removed `src.` prefix from all imports throughout the backend
  - Configured proper Python package structure in pyproject.toml
  - Added pytest configuration for correct module discovery
  - All tests passing with cleaner import paths

- ✅ **Comprehensive Test Suite Implementation**: Achieved 84% test coverage
  - Added full test coverage for all authentication endpoints (18 tests)
  - Comprehensive tests for document management API (20 tests)
  - Complete strategy API endpoint testing (17 tests)
  - Full backtest lifecycle management tests (21 tests)
  - Core authentication module tests (10 tests)
  - Security utilities test coverage (15 tests)
  - Auth service layer unit tests (12 tests)
  - User service layer tests (9 tests)
  - Repository pattern tests for all entities (40+ tests)
  - Schema validation tests for all DTOs (30+ tests)
  - Test coverage increased from 31% to 84%
  - Fixed numerous compatibility issues (Pydantic v2, imports, model fields)
  - Established async testing patterns with proper fixtures

- ✅ **Tilt.dev Development Environment** (July 23, 2025): Streamlined local development
  - Created comprehensive Tiltfile with live updates for all services
  - Configured automatic code sync for backend and frontend
  - Set up dependency auto-installation on package changes
  - Added development helper commands (test, lint, format) in Tilt UI
  - Implemented proper service dependencies and health checks
  - Updated Makefile with Tilt commands (make tilt, make tilt-down)
  - Enables rapid development with instant code updates without rebuilds
  - All services managed through unified dashboard at http://localhost:10350
  - **Fixed Tilt configuration issues** (July 23, 2025):
    - Corrected `fall_back_on` directive positioning in live_update steps
    - Removed invalid `port_forwards` from dc_resource calls
    - Removed unsupported `readiness_probe` arguments
    - Fixed `local_resource` serve_port parameter
    - Added image name warning suppression
    - Tilt now starts successfully with all services

### Sprint 2 Progress (July 23, 2025)
- ✅ **MinIO/S3 Document Storage Implementation**: Cloud-native document storage
  - Replaced local file storage with MinIO/S3 compatible storage
  - Created comprehensive storage service with aioboto3
  - Implemented user-isolated storage structure (user_id/unique_key.ext)
  - Added document download endpoint with streaming response
  - Implemented presigned URL generation for secure temporary access
  - Added automatic bucket creation on startup
  - Comprehensive error handling with automatic cleanup on failures
  - Updated Docker Compose with MinIO environment variables
  - Created storage service tests achieving 100% coverage
  - Added MinIO-specific document API integration tests
  - Successfully tested actual MinIO operations with test script
  - Created .env.example with all configuration options

- ✅ **PDF Parsing Service with LlamaIndex**: Advanced document text extraction
  - Implemented DocumentParserService using LlamaIndex framework
  - Integrated PyMuPDFReader for superior PDF parsing capabilities
  - Support for PDF, TXT, and Markdown file formats
  - Extracts both text content and document metadata
  - Page-by-page parsing capability for PDFs
  - Better handling of complex layouts, tables, and formatting
  - Automatic document chunking for LLM processing
  - Added extracted_text field to documents table
  - Updated document processing API endpoint
  - Created /documents/{id}/content endpoint for text retrieval
  - Page-specific content retrieval support
  - Successfully tested with both text and PDF documents

- ✅ **LLM Provider Integration - Anthropic Claude API**: AI service for strategy extraction
  - Implemented provider pattern with base abstract class for LLM providers
  - Created AnthropicProvider with Claude API integration
  - Built factory pattern for dynamic provider selection
  - Implemented LLMService as main interface for AI operations
  - Added comprehensive error handling with custom exceptions
  - Configured retry logic with exponential backoff
  - Created structured prompt templates for financial document analysis
  - Implemented JSON mode for structured strategy extraction
  - Added provider configuration with model selection (Claude 3.5 Sonnet)
  - Built complete test suite with mocked API responses
  - Prepared OpenAI and Google Gemini provider skeletons
  - Ready for strategy extraction from parsed documents

- ✅ **RabbitMQ Document Processing Pipeline**: Complete async processing implementation
  - Created message queue infrastructure with aio-pika
  - Built connection manager with automatic reconnection
  - Implemented message schemas with Pydantic validation
  - Created publisher for document processing messages
  - Built consumer/worker for processing documents
  - Integrated with storage, parser, and LLM services
  - Added retry logic with exponential backoff (max 3 retries)
  - Configured dead letter queue for failed messages
  - Updated document API endpoints to publish to queue
  - Created worker service in Docker Compose
  - Added worker to Tilt configuration
  - Implemented status tracking throughout pipeline
  - Built comprehensive test suite with ~95% coverage
  - Added end-to-end pipeline testing script

### What Exists
- Complete PRD with technical specifications and architecture
- BRD with business requirements and market analysis
- User stories document with 43 implementation-ready stories
- Memory bank system for maintaining project context
- CLAUDE.md with development guidelines
- **Backend**: FastAPI application with health endpoints
  - Dependencies: fastapi, uvicorn, pydantic, sqlalchemy, redis, httpx
  - Dev tools: pytest, ruff, mypy configured
  - Basic API structure at localhost:8000/api/v1
- **Frontend**: React/TypeScript application
  - Build tool: Vite for fast development
  - State: Redux Toolkit configured
  - UI: Material-UI installed
  - Router: React Router configured

### What's Been Completed (July 22-23, 2025)
- ✅ **Repository Pattern Implementation**: Full async data access layer
  - BaseRepository with type-safe generics for CRUD operations
  - Specialized repositories for User, Document, Strategy, Backtest
  - Unit of Work pattern for transaction management
  - FastAPI dependency injection integration
  - Comprehensive test structure

- ✅ **JWT Authentication System**: Enterprise-grade security
  - Access tokens (30min) and refresh tokens (7 days)
  - User registration and login endpoints
  - Role-based access control (Admin, Analyst, Viewer)
  - Password hashing with bcrypt
  - Token refresh and password change functionality
  - Protected route middleware

- ✅ **API Structure**: RESTful endpoints for all core resources
  - Health checks (/health, /api/v1/health)
  - Authentication endpoints (/api/v1/auth/*)
  - User management (/api/v1/users/*)
  - Document management (/api/v1/documents/*)
  - Strategy endpoints (/api/v1/strategies/*)
  - Backtest endpoints (/api/v1/backtests/*)
  - All with Pydantic validation and OpenAPI docs

- ✅ **Structured Logging System**: Production-ready observability
  - JSON structured logs with structlog
  - Environment-aware formatting (JSON/colored)
  - Request tracing with unique IDs
  - Performance monitoring middleware
  - Sensitive data automatic censoring
  - User context tracking for audit trails
  - Integration with ELK, Datadog, CloudWatch ready

- ✅ **Frontend Foundation**: Modern React architecture
  - React Router with protected routes
  - Redux Toolkit for state management
  - Material-UI component library integrated
  - Layout components (Header, Sidebar, Footer)
  - Authentication forms and flow
  - Feature pages scaffolding
  - TypeScript types for API integration
  - Axios service layer with interceptors

### What Doesn't Exist Yet (Sprint 2 Focus)
- **WebSocket Support**: Real-time updates for processing status
- **Backtesting**: Integration with backtesting frameworks
- **Advanced UI**: Interactive document viewer and strategy editor
- **Cloud Deployment**: Kubernetes manifests and Terraform configs
- **Monitoring Stack**: Prometheus/Grafana setup

## Next Steps - Sprint 2 (August 2025)

### Sprint 1 Achievements (Completed July 22, 2025) ✅
1. **Foundation Complete**: All 7 Sprint 1 tasks successfully completed
   - Database layer with migrations and models
   - Repository pattern with Unit of Work
   - JWT authentication with RBAC
   - Complete API structure for all resources
   - Structured logging system
   - Frontend foundation with routing and state
   - Development environment fully operational

### Sprint 2 Focus: AI Integration & Core Features

#### 1. **Document Processing Pipeline**
   - Implement MinIO/S3 document upload endpoint
   - Create PDF parsing service
   - Build document metadata extraction
   - Set up virus scanning integration
   - Implement document versioning

#### 2. **AI Service Implementation**
   - Integrate Anthropic Claude API
   - Build prompt engineering for strategy extraction
   - Implement retry logic with exponential backoff
   - Create caching layer for API responses
   - Build strategy validation and parsing

#### 3. **Event-Driven Architecture**
   - Set up RabbitMQ message publishers
   - Create document processing queue
   - Implement strategy extraction workers
   - Build event handlers for workflow orchestration
   - Add dead letter queue handling

#### 4. **Backtesting Integration**
   - Research and select backtesting framework
   - Create backtesting service skeleton
   - Implement basic strategy execution
   - Build performance metrics calculation
   - Create results storage and retrieval

#### 5. **Real-time Features**
   - Implement WebSocket support in FastAPI
   - Create real-time notification system
   - Build progress tracking for long operations
   - Implement live document processing updates
   - Add collaborative features foundation

#### 6. **Frontend Features**
   - Build document upload UI with drag-and-drop
   - Create document list with filtering/sorting
   - Implement strategy viewer component
   - Build basic dashboard with metrics
   - Add real-time status updates

### MVP Timeline (3-month target)

#### Completed (Month 1 - July 2025)
- ✅ Complete development environment
- ✅ Database and data access layer
- ✅ Authentication and authorization
- ✅ API structure and logging
- ✅ Frontend foundation

#### In Progress (Month 2 - August 2025)
- 🚧 Document processing pipeline
- 🚧 AI integration for strategy extraction
- 🚧 Event-driven architecture
- 🚧 Basic backtesting integration

#### Planned (Month 3 - September 2025)
- 📌 Performance optimization
- 📌 Advanced UI features
- 📌 Testing and bug fixes
- 📌 Beta deployment preparation

## Key Decisions Made

### Technology Choices
- **Backend**: Python with FastAPI (confirmed in PRD)
- **Frontend**: React with TypeScript
- **AI Integration**: Anthropic Claude API
- **Database**: PostgreSQL for persistence
- **Queue**: RabbitMQ for async processing
- **Cache**: Redis for performance

### Development Practices
- Use uv for Python package management (not pip/poetry)
- Follow Domain-Driven Design principles
- Implement Test-Driven Development
- Use pydantic for data validation
- Storybook for UI component development
- Python imports use clean paths without `src.` prefix (e.g., `from core.config import settings`)
- **Use Tilt.dev for local development environment** (implemented July 23, 2025)

## Current Blockers
None - implementation is progressing smoothly

## Technical Achievements (Sprint 1 Complete)

### Infrastructure Layer ✅
- **Docker Environment**: Multi-container setup with PostgreSQL, Redis, RabbitMQ, MinIO
- **CI/CD Pipeline**: GitHub Actions with testing, security scanning, and deployment
- **Development Tools**: Makefile, hot-reloading, environment configuration

### Data Access Layer ✅
- **Database Models**: User, Document, Strategy, Backtest with full relationships
- **Repository Pattern**: Type-safe generic CRUD with async support
- **Unit of Work**: Transaction management across multiple repositories
- **Migrations**: Alembic configured for schema evolution

### Security Layer ✅
- **JWT Authentication**: Access/refresh token system
- **RBAC**: Role-based access control (Admin, Analyst, Viewer)
- **Password Security**: Bcrypt hashing with secure defaults
- **API Protection**: Middleware for route authorization

### API Layer ✅
- **RESTful Design**: Consistent resource-based endpoints
- **Validation**: Pydantic schemas for all requests/responses
- **Documentation**: Auto-generated OpenAPI/Swagger
- **Error Handling**: Consistent error response format

### Observability Layer ✅
- **Structured Logging**: JSON logs with structlog
- **Request Tracing**: Unique IDs for distributed debugging
- **Performance Monitoring**: Automatic slow request detection
- **Security**: Automatic sensitive data censoring

### Frontend Layer ✅
- **Modern Stack**: React 18, TypeScript, Vite
- **State Management**: Redux Toolkit with auth slice
- **UI Library**: Material-UI for consistent design
- **Routing**: Protected routes with authentication flow
- **API Integration**: Axios with interceptors and type safety

## Important Patterns and Preferences

### Code Organization
- Microservices architecture as specified in PRD
- Clear separation between API, business logic, and data layers
- Event-driven communication between services

### Development Workflow
1. Start with core domain models
2. Build API endpoints with full validation
3. Implement async processing for heavy operations
4. Add UI components iteratively

### Quality Standards
- 80%+ test coverage achieved (currently at 84%)
- All APIs must have OpenAPI documentation
- Performance metrics tracked from day one
- Security scanning in CI/CD pipeline
- Test-Driven Development (TDD) approach
- Comprehensive async test patterns established

## Learning and Insights

### From Documentation Review
1. The project has exceptional planning depth with clear requirements
2. Market validation shows strong demand ($3.1B SAM)
3. Technical architecture is well-thought-out and scalable
4. User stories provide clear implementation guidance

### Key Success Factors for Sprint 2
1. **LLM Integration Quality**: 
   - Accurate strategy extraction from complex documents
   - Proper prompt engineering for consistency
   - Cost optimization through caching

2. **Processing Pipeline Performance**:
   - Sub-5 minute end-to-end processing
   - Robust error handling and recovery
   - Progress tracking for user feedback

3. **System Reliability**:
   - Message queue resilience
   - Graceful degradation
   - Comprehensive error logging

4. **User Experience**:
   - Intuitive document upload flow
   - Clear strategy visualization
   - Real-time processing feedback

### Risk Considerations
1. **LLM API Costs**: Need to optimize token usage for profitability
2. **Scaling Challenges**: Distributed backtesting requires careful orchestration
3. **Regulatory Compliance**: Financial services regulations vary by region
4. **Competition**: Fast-moving space with well-funded competitors

## Sprint 2 Current Status & Next Steps

### Completed (July 23, 2025)
- ✅ MinIO integration for file storage
- ✅ Document upload/download API with streaming
- ✅ Presigned URL generation
- ✅ PDF parsing and text extraction service
- ✅ Anthropic Claude API integration
- ✅ RabbitMQ document processing pipeline
- ✅ Comprehensive test coverage for all components

### Current Architecture
The document processing flow is now fully operational:
1. **Upload**: Documents uploaded to MinIO via API
2. **Queue**: Upload publishes message to RabbitMQ
3. **Worker**: Consumer processes document asynchronously
4. **Parse**: LlamaIndex extracts text and metadata
5. **Extract**: Claude API identifies investment strategies
6. **Store**: Results saved to PostgreSQL
7. **Status**: Updates tracked throughout pipeline

### Next Priority: Interactive UI Components
The backtesting integration is complete with backtesting.py library providing comprehensive performance metrics and multiple built-in strategies. The final Sprint 2 task is to build interactive UI components for the document viewer to display extracted strategies and backtest results.

### Remaining Sprint 2 Tasks
- [✓] WebSocket support for real-time updates - COMPLETED (July 23)
- [✓] Basic backtesting framework integration - COMPLETED (July 23)
- [ ] Document viewer UI component

**Sprint Progress: 7 of 8 tasks completed (87.5%)**

### Backtesting Integration Complete (July 23, 2025)
- ✅ **Backtesting Service**: Full async service with strategy execution
- ✅ **Strategy Factory**: 5 built-in strategies (SMA, RSI, Bollinger, Momentum, Custom)
- ✅ **Data Loader**: yfinance integration for all asset classes
- ✅ **Message Queue**: RabbitMQ integration with dedicated worker
- ✅ **API Endpoints**: Complete CRUD operations for backtests
- ✅ **Test Coverage**: Comprehensive tests with ~95% coverage
- ✅ **Infrastructure**: Docker Compose and Tilt configuration

### WebSocket Implementation Complete (July 23, 2025)
- ✅ **Backend WebSocket Infrastructure**:
  - Connection manager for handling multiple client connections
  - JWT-based authentication for secure connections
  - Typed notification system for all document events
  - Integration with document processing pipeline

- ✅ **Real-time Notifications**:
  - Document upload status (started/completed)
  - Processing progress with percentage and messages
  - Strategy extraction notifications
  - Error handling with detailed messages

- ✅ **Frontend Integration**:
  - WebSocket service with auto-reconnection
  - React hooks for easy component integration
  - Live progress bars in document list
  - Toast notifications for important events

## Development Guidelines
- Continue TDD approach with high test coverage
- Maintain structured logging for all new features
- Follow established patterns (Repository, Service, etc.)
- Update API documentation as endpoints are added
- Keep memory bank updated with significant changes