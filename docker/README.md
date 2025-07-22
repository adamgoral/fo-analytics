# Docker Development Environment

This directory contains the Docker configuration for the FO Analytics development environment.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Make (optional, for using Makefile commands)

## Quick Start

1. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

2. Start all services:
   ```bash
   make up
   # or without Make:
   docker-compose up -d
   ```

3. Check service status:
   ```bash
   make ps
   # or without Make:
   docker-compose ps
   ```

## Services

- **PostgreSQL** (port 5432): Main database
- **Redis** (port 6379): Cache and session storage
- **RabbitMQ** (ports 5672, 15672): Message broker with management UI
- **Backend API** (port 8000): FastAPI application
- **Frontend** (port 5173): React application
- **MinIO** (ports 9000, 9001): S3-compatible object storage
- **pgAdmin** (port 5050): PostgreSQL management tool (optional)

## Access Points

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- RabbitMQ Management: http://localhost:15672 (user: fo_user, pass: fo_password)
- MinIO Console: http://localhost:9001 (user: minioadmin, pass: minioadmin)
- pgAdmin: http://localhost:5050 (when using tools profile)

## Common Commands

```bash
# Start services
make up

# Start with tools (pgAdmin)
make up-tools

# View logs
make logs
make logs-backend
make logs-frontend

# Access containers
make shell-backend
make shell-frontend

# Database access
make db-shell

# Redis CLI
make redis-cli

# Stop services
make down

# Clean everything (including volumes)
make clean
```

## Development Workflow

1. The backend and frontend containers mount local directories for hot reloading
2. Backend changes are automatically detected by uvicorn
3. Frontend changes are automatically detected by Vite
4. Database migrations should be run inside the backend container

## Troubleshooting

- If services fail to start, check logs: `docker-compose logs [service-name]`
- For permission issues, ensure Docker daemon is running with proper permissions
- If ports are already in use, either stop conflicting services or modify ports in docker-compose.yml