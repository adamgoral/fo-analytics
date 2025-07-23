.PHONY: help up down build logs ps clean restart shell-backend shell-frontend db-shell redis-cli tilt tilt-down tilt-logs

help:
	@echo "Available commands:"
	@echo ""
	@echo "Docker Compose Commands:"
	@echo "  make up              - Start all services"
	@echo "  make up-tools        - Start all services including tools (pgAdmin)"
	@echo "  make down            - Stop all services"
	@echo "  make build           - Build all Docker images"
	@echo "  make logs            - Show logs for all services"
	@echo "  make logs-backend    - Show backend logs"
	@echo "  make logs-frontend   - Show frontend logs"
	@echo "  make ps              - List running containers"
	@echo "  make clean           - Remove all containers and volumes"
	@echo "  make restart         - Restart all services"
	@echo "  make shell-backend   - Open shell in backend container"
	@echo "  make shell-frontend  - Open shell in frontend container"
	@echo "  make db-shell        - Open PostgreSQL shell"
	@echo "  make redis-cli       - Open Redis CLI"
	@echo ""
	@echo "Tilt Development Commands:"
	@echo "  make tilt            - Start development environment with Tilt"
	@echo "  make tilt-down       - Stop Tilt development environment"
	@echo "  make tilt-logs       - Stream logs from all Tilt services"

# Start services
up:
	docker-compose up -d

up-tools:
	docker-compose --profile tools up -d

# Stop services
down:
	docker-compose down

# Build images
build:
	docker-compose build

# View logs
logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

# Container status
ps:
	docker-compose ps

# Clean everything
clean:
	docker-compose down -v
	docker system prune -f

# Restart services
restart:
	docker-compose restart

# Shell access
shell-backend:
	docker-compose exec backend /bin/bash

shell-frontend:
	docker-compose exec frontend /bin/sh

# Database access
db-shell:
	docker-compose exec postgres psql -U fo_user -d fo_analytics

# Redis access
redis-cli:
	docker-compose exec redis redis-cli

# Development setup
setup:
	@echo "Setting up development environment..."
	@cp .env.example .env
	@echo "Please edit .env file with your configuration"
	@echo "Then run 'make up' to start services"

# Tilt commands for development
tilt:
	@echo "Starting Tilt development environment..."
	@echo "Access Tilt UI at http://localhost:10350"
	@echo "Press Ctrl+C to access the web interface"
	tilt up

tilt-down:
	@echo "Stopping Tilt development environment..."
	tilt down

tilt-logs:
	@echo "Streaming Tilt logs..."
	tilt up --stream