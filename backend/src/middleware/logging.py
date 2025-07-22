"""
Request logging middleware for the FO Analytics platform.

This middleware logs all incoming requests and outgoing responses,
including request details, response status, and timing information.
It also adds request IDs for distributed tracing.
"""

import time
import uuid
from typing import Callable, Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.utils.logging import (
    logger,
    set_request_id,
    set_user_context,
    clear_context,
    LoggerAdapter,
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    
    Features:
    - Generates unique request IDs for tracing
    - Logs request method, path, headers, and query parameters
    - Logs response status code and duration
    - Adds request ID to response headers
    - Handles exceptions gracefully
    """
    
    def __init__(
        self,
        app: ASGIApp,
        *,
        skip_paths: Optional[set[str]] = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
    ):
        """
        Initialize the logging middleware.
        
        Args:
            app: The ASGI application
            skip_paths: Set of paths to skip logging (e.g., health checks)
            log_request_body: Whether to log request bodies (caution: may contain sensitive data)
            log_response_body: Whether to log response bodies (caution: may be large)
        """
        super().__init__(app)
        self.skip_paths = skip_paths or {"/health", "/api/v1/health", "/metrics"}
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and log relevant information."""
        # Skip logging for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Set request ID in context for all logs in this request
        set_request_id(request_id)
        
        # Extract request information
        request_info = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_host": request.client.host if request.client else None,
            "client_port": request.client.port if request.client else None,
        }
        
        # Log headers (excluding sensitive ones)
        safe_headers = self._get_safe_headers(dict(request.headers))
        if safe_headers:
            request_info["headers"] = safe_headers
        
        # Extract user context if available (from JWT or session)
        user_id = request.state.__dict__.get("user_id")
        username = request.state.__dict__.get("username")
        if user_id or username:
            set_user_context(user_id=user_id, username=username)
            request_info["user_id"] = user_id
            request_info["username"] = username
        
        # Log the incoming request
        logger.info("request_started", **request_info)
        
        # Track request timing
        start_time = time.perf_counter()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate request duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log the response
            response_info = {
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            }
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Log based on status code
            if response.status_code >= 500:
                logger.error("request_failed", **response_info)
            elif response.status_code >= 400:
                logger.warning("request_client_error", **response_info)
            else:
                logger.info("request_completed", **response_info)
            
            return response
            
        except Exception as e:
            # Calculate duration even for failed requests
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log the exception
            logger.error(
                "request_exception",
                request_id=request_id,
                duration_ms=round(duration_ms, 2),
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )
            
            # Re-raise the exception to be handled by FastAPI
            raise
            
        finally:
            # Clear context to avoid leaking between requests
            clear_context()
    
    def _get_safe_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Filter out sensitive headers before logging.
        
        Args:
            headers: The request headers
            
        Returns:
            Dictionary of headers safe for logging
        """
        sensitive_headers = {
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
            "x-csrf-token",
        }
        
        return {
            key: value if key.lower() not in sensitive_headers else "***REDACTED***"
            for key, value in headers.items()
        }


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware specifically for performance logging.
    
    This middleware tracks detailed performance metrics for each request,
    useful for identifying bottlenecks and optimizing response times.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        *,
        slow_request_threshold_ms: float = 1000.0,
    ):
        """
        Initialize the performance logging middleware.
        
        Args:
            app: The ASGI application
            slow_request_threshold_ms: Threshold for logging slow requests
        """
        super().__init__(app)
        self.slow_request_threshold_ms = slow_request_threshold_ms
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track and log request performance metrics."""
        # Use LoggerAdapter for performance tracking
        log_adapter = LoggerAdapter(logger)
        
        # Get request ID if available
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Track detailed timing
        timings = {
            "start": time.perf_counter(),
        }
        
        with log_adapter.performance(f"http_{request.method}_{request.url.path}"):
            response = await call_next(request)
            
        # Calculate total duration
        total_duration_ms = (time.perf_counter() - timings["start"]) * 1000
        
        # Log slow requests
        if total_duration_ms > self.slow_request_threshold_ms:
            logger.warning(
                "slow_request",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=round(total_duration_ms, 2),
                threshold_ms=self.slow_request_threshold_ms,
            )
        
        # Add performance headers to response
        response.headers["X-Response-Time"] = f"{total_duration_ms:.2f}ms"
        
        return response


def create_request_id_middleware() -> Callable:
    """
    Create a simple middleware that ensures all requests have a request ID.
    
    This is useful when you want request ID functionality without full logging.
    """
    async def request_id_middleware(request: Request, call_next: Callable) -> Response:
        # Check if request already has an ID (from headers)
        request_id = request.headers.get("X-Request-ID")
        
        # Generate new ID if needed
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Set in context
        set_request_id(request_id)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
        finally:
            clear_context()
    
    return request_id_middleware


# Export middleware classes and functions
__all__ = [
    "RequestLoggingMiddleware",
    "PerformanceLoggingMiddleware",
    "create_request_id_middleware",
]