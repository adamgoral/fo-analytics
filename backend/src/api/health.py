from fastapi import APIRouter

from src.utils.logging import logger, LoggerAdapter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    logger.debug("health_check_called")
    return {
        "status": "healthy",
        "service": "fo-analytics-backend"
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint that verifies all dependencies are available.
    
    This endpoint demonstrates how to use the performance logger for
    tracking individual operations within an endpoint.
    """
    log_adapter = LoggerAdapter(logger)
    
    # Check database connectivity
    db_status = "unknown"
    with log_adapter.performance("database_health_check"):
        # In a real implementation, you would check actual database connection
        # For now, we'll simulate it
        db_status = "connected"
    
    # Check cache connectivity  
    cache_status = "unknown"
    with log_adapter.performance("cache_health_check"):
        # In a real implementation, you would check actual Redis connection
        # For now, we'll simulate it
        cache_status = "connected"
    
    logger.info(
        "readiness_check_completed",
        database_status=db_status,
        cache_status=cache_status,
    )
    
    return {
        "status": "ready",
        "database": db_status,
        "cache": cache_status
    }