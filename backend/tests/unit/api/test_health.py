"""Tests for health check API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
class TestHealthAPI:
    """Test health check API endpoints."""

    async def test_health_check(self, async_client: AsyncClient):
        """Test basic health check endpoint."""
        response = await async_client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "fo-analytics-backend"
        
    async def test_readiness_check(self, async_client: AsyncClient):
        """Test readiness check endpoint."""
        response = await async_client.get("/api/v1/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"
        assert data["cache"] == "connected"
        
    async def test_readiness_check_performance_logging(self, async_client: AsyncClient):
        """Test that readiness check logs performance metrics."""
        response = await async_client.get("/api/v1/ready")
        
        assert response.status_code == 200
        # The middleware should add performance headers
        assert "x-response-time" in response.headers