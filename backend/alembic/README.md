# Database Migrations

This directory contains database migrations managed by Alembic.

## Prerequisites

1. Ensure PostgreSQL is running (either locally or via Docker)
2. Update DATABASE_URL in your .env file or environment variables

## Common Commands

### Create a new migration
```bash
uv run alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
uv run alembic upgrade head
```

### Rollback one migration
```bash
uv run alembic downgrade -1
```

### View migration history
```bash
uv run alembic history
```

### View current migration
```bash
uv run alembic current
```

## Docker Usage

When running with Docker, the database URL should use the service name:
```
postgresql+asyncpg://fo_user:fo_password@postgres:5432/fo_analytics
```

## First Time Setup

1. Start the database service:
   ```bash
   make up  # or docker compose up -d postgres
   ```

2. Run the initial migration:
   ```bash
   uv run alembic upgrade head
   ```

## Models

The following models are defined:
- User: Authentication and user management
- Document: Uploaded documents and their processing status
- Strategy: Trading strategies extracted from documents
- Backtest: Backtest results for strategies