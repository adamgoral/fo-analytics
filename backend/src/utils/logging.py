"""
Structured logging configuration for the FO Analytics platform.

This module configures structlog for JSON-formatted logs in production
and colored console logs in development. It includes request ID context
tracking and performance logging capabilities.
"""

import logging
import sys
import time
from datetime import datetime, timezone
from enum import StrEnum, auto
from typing import Any, Dict, Optional, Protocol, TypeVar

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars, merge_contextvars
from structlog.processors import CallsiteParameter, CallsiteParameterAdder
from structlog.types import Processor

from src.core.config import settings


class LogLevel(StrEnum):
    """Log levels as string enum for consistency."""
    
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class TimeFormatter(Protocol):
    """Protocol for time formatting functions."""
    
    def __call__(self, timestamp: float) -> str: ...


def add_timestamp(_: Any, __: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add ISO format timestamp to log events."""
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    return event_dict


def add_log_level(_, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add log level to the event dict."""
    event_dict["level"] = method_name.upper()
    return event_dict


def add_app_context(_: Any, __: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add application context to all logs."""
    event_dict["app_name"] = settings.app_name
    event_dict["app_version"] = settings.app_version
    event_dict["environment"] = "development" if settings.debug else "production"
    return event_dict


def drop_color_message_key(_: Any, __: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Remove color message key for production logs."""
    event_dict.pop("color_message", None)
    return event_dict


def censor_sensitive_data(_: Any, __: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Censor sensitive data in logs."""
    sensitive_keys = {"password", "token", "secret", "api_key", "authorization"}
    
    def _censor_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        censored = {}
        for key, value in d.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                censored[key] = "***REDACTED***"
            elif isinstance(value, dict):
                censored[key] = _censor_dict(value)
            else:
                censored[key] = value
        return censored
    
    return _censor_dict(event_dict)


def get_console_renderer() -> Processor:
    """Get the appropriate console renderer based on environment."""
    if settings.debug:
        # Colored output for development
        return structlog.dev.ConsoleRenderer(colors=True)
    else:
        # JSON output for production
        return structlog.processors.JSONRenderer()


def configure_logging() -> None:
    """
    Configure structured logging for the application.
    
    Sets up different logging configurations for development and production:
    - Development: Colored console output with detailed information
    - Production: JSON formatted logs for log aggregation systems
    """
    # Determine log level based on environment
    log_level = logging.DEBUG if settings.debug else logging.INFO
    
    # Configure Python's logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Common processors for all environments
    common_processors: list[Processor] = [
        add_app_context,
        add_timestamp,
        add_log_level,
        merge_contextvars,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        censor_sensitive_data,
    ]
    
    # Environment-specific processors
    if settings.debug:
        # Development processors
        processors = common_processors + [
            CallsiteParameterAdder(
                parameters=[
                    CallsiteParameter.FILENAME,
                    CallsiteParameter.FUNC_NAME,
                    CallsiteParameter.LINENO,
                ]
            ),
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # Production processors
        processors = common_processors + [
            drop_color_message_key,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Initialize logger
logger = structlog.get_logger()


# Context management functions
def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID in logging context."""
    bind_contextvars(correlation_id=correlation_id)


def set_request_id(request_id: str) -> None:
    """Set request ID in logging context."""
    bind_contextvars(request_id=request_id)


def set_user_context(user_id: Optional[str] = None, username: Optional[str] = None) -> None:
    """Set user context in logging."""
    context = {}
    if user_id:
        context["user_id"] = user_id
    if username:
        context["username"] = username
    if context:
        bind_contextvars(**context)


def clear_context() -> None:
    """Clear all logging context."""
    clear_contextvars()


class LoggerAdapter:
    """
    Adapter class for adding performance logging capabilities.
    
    Usage:
        log = LoggerAdapter(logger)
        with log.performance("database_query"):
            # Perform database operation
            pass
    """
    
    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger
    
    def performance(self, operation: str):
        """Context manager for performance logging."""
        return PerformanceLogger(self.logger, operation)


class PerformanceLogger:
    """Context manager for logging operation performance."""
    
    def __init__(self, logger: structlog.BoundLogger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        self.logger.debug(f"{self.operation}_started", operation=self.operation)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration_ms = (time.perf_counter() - self.start_time) * 1000
            
            log_data = {
                "operation": self.operation,
                "duration_ms": round(duration_ms, 2),
                "success": exc_type is None
            }
            
            if exc_type is not None:
                log_data["error_type"] = exc_type.__name__
                log_data["error_message"] = str(exc_val)
                self.logger.error(f"{self.operation}_failed", **log_data)
            else:
                self.logger.info(f"{self.operation}_completed", **log_data)


# API endpoint performance decorator
def log_endpoint_performance(func):
    """Decorator for logging API endpoint performance."""
    async def wrapper(*args, **kwargs):
        endpoint_name = func.__name__
        log_adapter = LoggerAdapter(logger)
        
        with log_adapter.performance(f"endpoint_{endpoint_name}"):
            result = await func(*args, **kwargs)
            return result
    
    return wrapper


# Export main components
__all__ = [
    "configure_logging",
    "logger",
    "set_correlation_id",
    "set_request_id",
    "set_user_context",
    "clear_context",
    "LoggerAdapter",
    "log_endpoint_performance",
    "LogLevel",
]