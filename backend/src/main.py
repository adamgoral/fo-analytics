from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.api.health import router as health_router
from src.api.users import router as users_router
from src.api.auth import router as auth_router
from src.api.strategies import router as strategies_router
from src.api.backtests import router as backtests_router
from src.api.documents import router as documents_router
from src.utils.logging import configure_logging, logger
from src.middleware.logging import RequestLoggingMiddleware, PerformanceLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Configure application lifespan events.
    
    This function runs on startup and shutdown, handling:
    - Logging configuration
    - Database connections
    - Background tasks
    """
    # Configure logging on startup
    configure_logging()
    logger.info(
        "application_started",
        app_name=settings.app_name,
        version=settings.app_version,
        environment="development" if settings.debug else "production",
    )
    
    yield
    
    # Cleanup on shutdown
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        lifespan=lifespan,
    )
    
    # Add performance logging middleware (before request logging)
    app.add_middleware(
        PerformanceLoggingMiddleware,
        slow_request_threshold_ms=500.0,  # Log requests slower than 500ms
    )
    
    # Add request logging middleware
    app.add_middleware(
        RequestLoggingMiddleware,
        skip_paths={"/health", f"{settings.api_prefix}/health", "/metrics"},
        log_request_body=False,  # Don't log request bodies by default
        log_response_body=False,  # Don't log response bodies by default
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(users_router, prefix=settings.api_prefix)
    app.include_router(strategies_router, prefix=settings.api_prefix)
    app.include_router(backtests_router, prefix=settings.api_prefix)
    app.include_router(documents_router, prefix=settings.api_prefix)
    
    return app


app = create_app()