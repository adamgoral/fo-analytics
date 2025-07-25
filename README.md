# Front Office Analytics AI Platform

An AI-powered platform for analyzing financial documents and extracting investment strategies, with integrated backtesting capabilities.

## Overview

The Front Office Analytics platform helps financial institutions automate the extraction and analysis of investment strategies from various document types (PDFs, research reports, etc.) using advanced AI models. It provides comprehensive backtesting capabilities to validate strategies before implementation.

## Features

- **Document Processing**: Upload and parse financial documents (PDF, TXT, DOC)
- **AI Strategy Extraction**: Automatically extract investment strategies using Claude AI
- **Backtesting Engine**: Test strategies with historical data across multiple asset classes
- **Portfolio Optimization**: Advanced portfolio construction with multiple optimization methods
- **Real-time Updates**: WebSocket integration for live processing status
- **AI Chat Interface**: Natural language interaction for strategy refinement
- **Interactive Analytics**: Charts and visualizations for performance analysis

## Tech Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy, Pydantic
- **Frontend**: React 18, TypeScript, Redux Toolkit, Material-UI
- **Database**: PostgreSQL 15
- **Message Queue**: RabbitMQ
- **Cache**: Redis
- **Storage**: MinIO (S3-compatible)
- **AI**: Anthropic Claude 3.5 Sonnet
- **Development**: Docker, Tilt.dev

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development)
- Node.js 18+ (for frontend development)
- Anthropic API key (see [API Keys Setup](docs/API_KEYS_SETUP.md))

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd fo-analytics
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
   ```
   See [API Keys Setup Guide](docs/API_KEYS_SETUP.md) for detailed instructions.

3. **Start all services with Docker Compose**:
   ```bash
   make dev
   ```

4. **Access the application**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000/api/v1/docs
   - RabbitMQ Management: http://localhost:15672 (guest/guest)
   - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)

### Development with Tilt

For a better development experience with hot-reloading:

```bash
make tilt
```

This starts the Tilt dashboard at http://localhost:10350 with live updates for all services.

## Project Structure

```
fo-analytics/
├── backend/              # FastAPI backend application
│   ├── src/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core utilities and config
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   └── workers/     # Async workers
│   └── tests/           # Backend tests
├── frontend/            # React frontend application
│   ├── src/
│   │   ├── components/  # Reusable components
│   │   ├── features/    # Feature modules
│   │   ├── services/    # API services
│   │   └── store/       # Redux store
│   └── tests/           # Frontend tests
├── docs/                # Documentation
├── memory-bank/         # Project context and decisions
└── docker-compose.yml   # Docker services configuration
```

## Development

### Backend Development

```bash
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
uv run pytest
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
make test-backend

# Frontend tests
make test-frontend

# All tests
make test
```

### Code Quality

```bash
# Linting
make lint

# Formatting
make format
```

## API Documentation

Once the backend is running, you can access:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## Database Migrations

```bash
# Create a new migration
make migration message="Add new field"

# Apply migrations
make migrate
```

## Troubleshooting

### Worker Service Issues

If the worker service fails to start, check:
1. API key is set in `.env` file
2. Worker logs: `docker-compose logs -f worker`
3. See [API Keys Setup Guide](docs/API_KEYS_SETUP.md)

### Port Conflicts

If you encounter port conflicts:
- Frontend runs on port 5173 (not 3000)
- Backend API on port 8000
- PostgreSQL on port 5432
- Redis on port 6379
- RabbitMQ on ports 5672 (AMQP) and 15672 (Management)

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[License information here]

## Support

For issues and questions:
- Check the [Memory Bank](memory-bank/) for project context
- Review existing GitHub issues
- Contact the development team