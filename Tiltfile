# -*- mode: Python -*-
# Tiltfile for Front Office Analytics AI Platform
# This file configures the development environment using Tilt.dev

# Load existing docker-compose configuration
docker_compose('docker-compose.yml')

# Configure live updates for backend service
docker_build(
    'fo-analytics-backend',
    './backend',
    dockerfile='./backend/Dockerfile.dev',
    live_update=[
        # Sync all Python source code
        sync('./backend/app', '/app/app'),
        sync('./backend/tests', '/app/tests'),
        sync('./backend/alembic', '/app/alembic'),
        
        # Re-install dependencies when requirements change
        run('cd /app && uv pip sync requirements.txt', 
            trigger=['./backend/requirements.txt']),
        
        # Run migrations when alembic versions change
        run('cd /app && alembic upgrade head', 
            trigger=['./backend/alembic/versions/']),
        
        # Restart the container to pick up changes
        restart_container()
    ],
    ignore=['**/__pycache__', '**/*.pyc', '.pytest_cache', '.coverage', 'htmlcov']
)

# Configure live updates for frontend service
docker_build(
    'fo-analytics-frontend',
    './frontend',
    dockerfile='./frontend/Dockerfile.dev',
    live_update=[
        # Sync source files for hot module replacement
        sync('./frontend/src', '/app/src'),
        sync('./frontend/public', '/app/public'),
        sync('./frontend/index.html', '/app/index.html'),
        sync('./frontend/vite.config.ts', '/app/vite.config.ts'),
        
        # Re-install dependencies when package.json changes
        run('cd /app && npm install', 
            trigger=['./frontend/package.json', './frontend/package-lock.json']),
        
        # Fall back to full rebuild for major dependency changes
        fall_back_on(['./frontend/package.json', './frontend/package-lock.json'])
    ],
    ignore=['node_modules', 'dist', 'build', '.vite']
)

# Configure backend service resource
dc_resource(
    'backend',
    port_forwards=['8000:8000'],  # FastAPI
    labels=['api', 'python'],
    resource_deps=['postgres', 'redis', 'rabbitmq', 'minio'],
    readiness_probe=probe(
        http_get=http_get_action(port=8000, path='/health'),
        period_secs=10,
        failure_threshold=3
    )
)

# Configure frontend service resource
dc_resource(
    'frontend',
    port_forwards=['3000:3000'],  # React dev server
    labels=['ui', 'react'],
    resource_deps=['backend'],
    readiness_probe=probe(
        http_get=http_get_action(port=3000),
        period_secs=10,
        failure_threshold=3
    )
)

# Configure database resources
dc_resource(
    'postgres',
    port_forwards=['5432:5432'],
    labels=['database'],
    readiness_probe=probe(
        exec=exec_action(['pg_isready', '-U', 'postgres']),
        period_secs=5
    )
)

dc_resource(
    'redis',
    port_forwards=['6379:6379'],
    labels=['cache'],
    readiness_probe=probe(
        exec=exec_action(['redis-cli', 'ping']),
        period_secs=5
    )
)

dc_resource(
    'rabbitmq',
    port_forwards=['5672:5672', '15672:15672'],  # AMQP and Management UI
    labels=['messaging']
)

dc_resource(
    'minio',
    port_forwards=['9000:9000', '9001:9001'],  # API and Console
    labels=['storage']
)

# Local development helpers

# Run backend tests
local_resource(
    'test-backend',
    cmd='docker-compose exec -T backend uv run pytest -v',
    deps=['./backend/app', './backend/tests'],
    labels=['tests', 'backend'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL
)

# Run backend tests with coverage
local_resource(
    'test-coverage',
    cmd='docker-compose exec -T backend uv run pytest --cov=app --cov-report=term-missing --cov-report=html',
    deps=['./backend/app', './backend/tests'],
    labels=['tests', 'backend'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL
)

# Format Python code
local_resource(
    'format-python',
    cmd='docker-compose exec -T backend uv run ruff format .',
    deps=['./backend'],
    labels=['quality', 'backend'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL
)

# Lint Python code
local_resource(
    'lint-python',
    cmd='docker-compose exec -T backend uv run ruff check . --fix',
    deps=['./backend'],
    labels=['quality', 'backend'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL
)

# Type check Python code
local_resource(
    'typecheck-python',
    cmd='docker-compose exec -T backend uv run mypy app',
    deps=['./backend/app'],
    labels=['quality', 'backend'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL
)

# Run frontend tests
local_resource(
    'test-frontend',
    cmd='docker-compose exec -T frontend npm test',
    deps=['./frontend/src', './frontend/tests'],
    labels=['tests', 'frontend'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL
)

# Lint frontend code
local_resource(
    'lint-frontend',
    cmd='docker-compose exec -T frontend npm run lint',
    deps=['./frontend/src'],
    labels=['quality', 'frontend'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL
)

# Build frontend for production
local_resource(
    'build-frontend',
    cmd='docker-compose exec -T frontend npm run build',
    deps=['./frontend/src', './frontend/public'],
    labels=['build', 'frontend'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL
)

# Run database migrations
local_resource(
    'migrate',
    cmd='docker-compose exec -T backend alembic upgrade head',
    labels=['database'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL
)

# Create new migration
local_resource(
    'make-migration',
    cmd='read -p "Migration name: " name && docker-compose exec -T backend alembic revision --autogenerate -m "$name"',
    labels=['database'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL
)

# Storybook for UI component development
local_resource(
    'storybook',
    serve_cmd='cd frontend && npm run storybook',
    serve_port=6006,
    labels=['ui-dev', 'frontend'],
    auto_init=False,
    trigger_mode=TRIGGER_MODE_MANUAL,
    deps=['./frontend/src']
)

# Print helpful information
print("""
🚀 Front Office Analytics Development Environment

Services:
  - Backend API: http://localhost:8000
  - Frontend UI: http://localhost:3000
  - API Documentation: http://localhost:8000/docs
  - RabbitMQ Management: http://localhost:15672 (guest/guest)
  - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)

Useful commands:
  - tilt up              # Start all services
  - tilt up backend      # Start only backend and dependencies
  - tilt down            # Stop all services
  - tilt trigger test-backend    # Run backend tests
  - tilt trigger test-coverage   # Run tests with coverage
  - tilt trigger format-python   # Format Python code
  - tilt trigger storybook       # Start Storybook

Press Ctrl+C in Tilt UI to access the web interface at http://localhost:10350
""")