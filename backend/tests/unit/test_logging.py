"""
Unit tests for the logging configuration and middleware.
"""

import json
import time
import uuid
from io import StringIO
from unittest.mock import Mock, patch

import pytest
import structlog
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.utils.logging import (
    LogLevel,
    LoggerAdapter,
    PerformanceLogger,
    add_app_context,
    add_timestamp,
    censor_sensitive_data,
    clear_context,
    configure_logging,
    logger,
    set_correlation_id,
    set_request_id,
    set_user_context,
)
from src.middleware.logging import (
    RequestLoggingMiddleware,
    PerformanceLoggingMiddleware,
    create_request_id_middleware,
)


class TestLoggingConfiguration:
    """Test logging configuration functions."""
    
    def test_add_timestamp(self):
        """Test timestamp addition to log events."""
        event_dict = {}
        result = add_timestamp(None, None, event_dict)
        
        assert "timestamp" in result
        # Check for UTC timezone (either Z or +00:00)
        assert result["timestamp"].endswith(("Z", "+00:00"))
    
    def test_add_app_context(self):
        """Test application context addition."""
        with patch("src.utils.logging.settings") as mock_settings:
            mock_settings.app_name = "Test App"
            mock_settings.app_version = "1.0.0"
            mock_settings.debug = True
            
            event_dict = {}
            result = add_app_context(None, None, event_dict)
            
            assert result["app_name"] == "Test App"
            assert result["app_version"] == "1.0.0"
            assert result["environment"] == "development"
    
    def test_censor_sensitive_data(self):
        """Test sensitive data censoring."""
        event_dict = {
            "user": "john",
            "password": "secret123",
            "api_key": "key123",
            "nested": {
                "token": "token456",
                "safe_data": "visible"
            }
        }
        
        result = censor_sensitive_data(None, None, event_dict)
        
        assert result["user"] == "john"
        assert result["password"] == "***REDACTED***"
        assert result["api_key"] == "***REDACTED***"
        assert result["nested"]["token"] == "***REDACTED***"
        assert result["nested"]["safe_data"] == "visible"


class TestContextManagement:
    """Test logging context management functions."""
    
    def test_set_and_clear_context(self):
        """Test setting and clearing context variables."""
        # Set various context values
        set_request_id("req_123")
        set_correlation_id("corr_456")
        set_user_context(user_id="user_789", username="testuser")
        
        # Context should be bound
        # Note: Testing context vars requires proper setup
        
        # Clear context
        clear_context()
        
        # Context should be cleared
        # Note: Actual verification would require checking structlog's context


class TestLoggerAdapter:
    """Test the LoggerAdapter class."""
    
    def test_performance_logger_success(self):
        """Test performance logger for successful operations."""
        mock_logger = Mock()
        adapter = LoggerAdapter(mock_logger)
        
        with adapter.performance("test_operation"):
            time.sleep(0.01)  # Simulate some work
        
        # Check that start and completion were logged
        assert mock_logger.debug.called
        assert mock_logger.info.called
        
        # Check the completion log includes duration
        info_call_args = mock_logger.info.call_args
        assert "test_operation_completed" in info_call_args[0]
        assert "duration_ms" in info_call_args[1]
        assert info_call_args[1]["success"] is True
    
    def test_performance_logger_failure(self):
        """Test performance logger for failed operations."""
        mock_logger = Mock()
        adapter = LoggerAdapter(mock_logger)
        
        with pytest.raises(ValueError):
            with adapter.performance("test_operation"):
                raise ValueError("Test error")
        
        # Check that error was logged
        assert mock_logger.error.called
        error_call_args = mock_logger.error.call_args
        assert "test_operation_failed" in error_call_args[0]
        assert error_call_args[1]["success"] is False
        assert error_call_args[1]["error_type"] == "ValueError"


class TestRequestLoggingMiddleware:
    """Test request logging middleware."""
    
    @pytest.fixture
    def app(self):
        """Create a test FastAPI app with logging middleware."""
        app = FastAPI()
        
        app.add_middleware(
            RequestLoggingMiddleware,
            skip_paths={"/health"},
            log_request_body=False,
            log_response_body=False,
        )
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @app.get("/health")
        async def health_endpoint():
            return {"status": "ok"}
        
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        return app
    
    def test_request_logging(self, app):
        """Test that requests are logged properly."""
        client = TestClient(app)
        
        with patch("src.middleware.logging.logger") as mock_logger:
            response = client.get("/test")
            
            assert response.status_code == 200
            assert "X-Request-ID" in response.headers
            
            # Verify logging calls
            assert mock_logger.info.call_count >= 2  # start and complete
    
    def test_skip_paths(self, app):
        """Test that configured paths are skipped."""
        client = TestClient(app)
        
        with patch("src.middleware.logging.logger") as mock_logger:
            response = client.get("/health")
            
            assert response.status_code == 200
            # Should not log for skipped paths
            assert mock_logger.info.call_count == 0
    
    def test_error_logging(self, app):
        """Test that errors are logged properly."""
        client = TestClient(app)
        
        with patch("src.middleware.logging.logger") as mock_logger:
            with pytest.raises(ValueError):
                response = client.get("/error")
            
            # Should log the error
            assert mock_logger.error.called


class TestPerformanceLoggingMiddleware:
    """Test performance logging middleware."""
    
    @pytest.fixture
    def app(self):
        """Create a test app with performance middleware."""
        app = FastAPI()
        
        app.add_middleware(
            PerformanceLoggingMiddleware,
            slow_request_threshold_ms=50.0,
        )
        
        @app.get("/fast")
        async def fast_endpoint():
            return {"speed": "fast"}
        
        @app.get("/slow")
        async def slow_endpoint():
            time.sleep(0.1)  # 100ms
            return {"speed": "slow"}
        
        return app
    
    def test_performance_headers(self, app):
        """Test that performance headers are added."""
        client = TestClient(app)
        
        response = client.get("/fast")
        assert "X-Response-Time" in response.headers
        assert response.headers["X-Response-Time"].endswith("ms")
    
    def test_slow_request_logging(self, app):
        """Test that slow requests are logged."""
        client = TestClient(app)
        
        with patch("src.middleware.logging.logger") as mock_logger:
            response = client.get("/slow")
            
            # Should log slow request warning
            assert mock_logger.warning.called
            warning_args = mock_logger.warning.call_args
            assert "slow_request" in warning_args[0]


class TestLoggingIntegration:
    """Integration tests for logging system."""
    
    def test_json_output_format(self):
        """Test JSON output format in production mode."""
        output = StringIO()
        
        with patch("src.utils.logging.settings.debug", False):
            with patch("sys.stdout", output):
                configure_logging()
                test_logger = structlog.get_logger()
                test_logger.info("test_event", key="value")
        
        output_value = output.getvalue()
        # Should be valid JSON
        parsed = json.loads(output_value.strip())
        assert parsed["event"] == "test_event"
        assert parsed["key"] == "value"
        assert "timestamp" in parsed
        assert "level" in parsed


@pytest.mark.asyncio
class TestRequestIdMiddleware:
    """Test request ID middleware functionality."""
    
    async def test_create_request_id_middleware(self):
        """Test the request ID middleware factory."""
        middleware = create_request_id_middleware()
        
        # Mock request and call_next
        request = Mock(spec=Request)
        request.headers = {}
        
        async def call_next(req):
            return Mock(headers={})
        
        with patch("src.middleware.logging.set_request_id") as mock_set_id:
            response = await middleware(request, call_next)
            
            # Should set request ID
            assert mock_set_id.called
            # Should add header to response
            assert "X-Request-ID" in response.headers