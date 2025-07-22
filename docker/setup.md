# Docker Development Environment Setup

## Prerequisites

Before running the Docker environment, ensure you have:

1. **Docker Desktop** (recommended) or Docker Engine installed
   - [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - Verify installation: `docker --version`

2. **Docker Compose** (included with Docker Desktop)
   - Verify installation: `docker compose version`

## Quick Start

1. **Build the Docker images:**
   ```bash
   docker compose build
   ```

2. **Start all services:**
   ```bash
   docker compose up -d
   ```

3. **Check service status:**
   ```bash
   docker compose ps
   ```

## Services

The docker-compose.yml configures the following services:

| Service    | Port(s)      | Purpose                           |
|------------|--------------|-----------------------------------|
| backend    | 8000         | FastAPI application               |
| frontend   | 5173         | React development server          |
| postgres   | 5432         | PostgreSQL database               |
| redis      | 6379         | Redis cache                       |
| rabbitmq   | 5672, 15672  | Message broker (+ management UI)  |
| minio      | 9000, 9001   | S3-compatible storage (+ console) |
| pgadmin    | 5050         | Database management (optional)    |

## Development Workflow

### Using Make commands (if Make is installed):

```bash
# Start services
make up

# View logs
make logs-backend
make logs-frontend

# Access container shells
make shell-backend
make shell-frontend

# Database access
make db-shell

# Stop services
make down
```

### Using Docker Compose directly:

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Access container shells
docker compose exec backend /bin/bash
docker compose exec frontend /bin/sh

# Database access
docker compose exec postgres psql -U fo_user -d fo_analytics

# Stop services
docker compose down
```

## Environment Variables

Create a `.env` file in the project root with:

```env
# Database
DATABASE_URL=postgresql://fo_user:fo_password@localhost:5432/fo_analytics

# Redis
REDIS_URL=redis://localhost:6379

# RabbitMQ
RABBITMQ_URL=amqp://fo_user:fo_password@localhost:5672/

# MinIO
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
S3_ENDPOINT_URL=http://localhost:9000

# API
API_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
```

## Troubleshooting

### Port conflicts
If you get port binding errors, check if services are already running:
```bash
# Check what's using port 8000 (example)
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

### Container not starting
Check logs for specific service:
```bash
docker compose logs backend
```

### Clean slate
Remove all containers and volumes:
```bash
docker compose down -v
docker system prune -f
```

## Hot Reloading

Both backend and frontend support hot reloading:

- **Backend**: Changes to Python files automatically restart the server
- **Frontend**: Vite provides instant HMR (Hot Module Replacement)

The docker-compose.yml mounts local directories as volumes to enable this feature.

## Database Management

### Using pgAdmin (optional):
1. Start with tools profile: `docker compose --profile tools up -d`
2. Access pgAdmin at http://localhost:5050
3. Login: admin@fo-analytics.com / admin
4. Add server:
   - Host: postgres
   - Port: 5432
   - Username: fo_user
   - Password: fo_password

### Using psql CLI:
```bash
docker compose exec postgres psql -U fo_user -d fo_analytics
```

## Next Steps

After starting the Docker environment:

1. Backend API will be available at http://localhost:8000
2. API documentation at http://localhost:8000/docs
3. Frontend will be available at http://localhost:5173
4. RabbitMQ management UI at http://localhost:15672 (fo_user/fo_password)
5. MinIO console at http://localhost:9001 (minioadmin/minioadmin)