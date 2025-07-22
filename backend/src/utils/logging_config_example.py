"""
Example configurations for different logging scenarios.

This file demonstrates how to use the logging utilities in various
parts of the application.
"""

from utils.logging import logger, LoggerAdapter, log_endpoint_performance


# Basic logging examples
def basic_logging_examples():
    """Demonstrate basic logging at different levels."""
    
    # Debug level - detailed information for debugging
    logger.debug("processing_started", step="data_validation", records=100)
    
    # Info level - general informational messages
    logger.info("user_action", action="document_upload", file_size_mb=25.3)
    
    # Warning level - warning messages for potentially harmful situations
    logger.warning("rate_limit_approaching", current=95, limit=100, user_id="user123")
    
    # Error level - error messages for serious problems
    logger.error(
        "external_api_failed",
        service="anthropic",
        status_code=503,
        retry_count=3
    )
    
    # Critical level - critical problems that need immediate attention
    logger.critical(
        "database_connection_lost",
        host="primary-db.example.com",
        error="Connection timeout"
    )


# Structured data logging
def structured_data_example():
    """Demonstrate logging with structured data."""
    
    # Log complex objects
    strategy_data = {
        "id": "strat_123",
        "name": "Mean Reversion Strategy",
        "parameters": {
            "lookback_period": 20,
            "threshold": 2.0,
            "position_size": 0.1
        },
        "backtest_results": {
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.15,
            "total_return": 0.25
        }
    }
    
    logger.info("strategy_created", **strategy_data)
    
    # Log lists and nested structures
    logger.info(
        "batch_processing_complete",
        documents=["doc1.pdf", "doc2.pdf", "doc3.pdf"],
        processing_times_ms=[1200, 1500, 1100],
        total_strategies_extracted=15,
        extraction_metrics={
            "accuracy": 0.96,
            "confidence_scores": [0.95, 0.97, 0.94]
        }
    )


# Performance logging examples
def performance_logging_example():
    """Demonstrate performance logging patterns."""
    
    log_adapter = LoggerAdapter(logger)
    
    # Log database query performance
    with log_adapter.performance("database_query_strategies"):
        # Simulate database operation
        pass
    
    # Log external API call performance
    with log_adapter.performance("llm_api_call"):
        # Simulate API call
        pass
    
    # Nested performance logging
    with log_adapter.performance("document_processing"):
        # PDF parsing
        with log_adapter.performance("pdf_parsing"):
            pass
        
        # Text extraction
        with log_adapter.performance("text_extraction"):
            pass
        
        # Strategy analysis
        with log_adapter.performance("strategy_analysis"):
            pass


# Exception logging
def exception_logging_example():
    """Demonstrate exception logging patterns."""
    
    try:
        # Simulate some operation that might fail
        result = 1 / 0
    except ZeroDivisionError as e:
        logger.error(
            "calculation_failed",
            operation="portfolio_optimization",
            error_type=type(e).__name__,
            error_message=str(e),
            exc_info=True  # This will include the full traceback
        )
    
    # Log exceptions with context
    try:
        # Simulate file processing error
        raise FileNotFoundError("strategy_template.json not found")
    except FileNotFoundError as e:
        logger.error(
            "file_processing_error",
            file_path="strategy_template.json",
            operation="template_loading",
            user_id="user456",
            exc_info=True
        )


# Correlation and tracing example
def correlation_example():
    """Demonstrate correlation ID usage for distributed tracing."""
    
    from utils.logging import set_correlation_id
    
    # Set correlation ID for a distributed operation
    correlation_id = "corr_789abc"
    set_correlation_id(correlation_id)
    
    # All subsequent logs will include this correlation ID
    logger.info("document_upload_started", document_id="doc_123")
    logger.info("document_processed", pages=50)
    logger.info("strategies_extracted", count=3)
    
    # Correlation ID helps trace the entire flow across services


# Service layer logging pattern
class DocumentService:
    """Example service with comprehensive logging."""
    
    def __init__(self):
        self.logger = logger
        self.log_adapter = LoggerAdapter(logger)
    
    async def process_document(self, document_id: str, user_id: str):
        """Process a document with detailed logging."""
        
        self.logger.info(
            "document_processing_started",
            document_id=document_id,
            user_id=user_id
        )
        
        try:
            # Validate document
            with self.log_adapter.performance("document_validation"):
                await self._validate_document(document_id)
            
            # Extract text
            with self.log_adapter.performance("text_extraction"):
                text = await self._extract_text(document_id)
                self.logger.debug(
                    "text_extracted",
                    document_id=document_id,
                    character_count=len(text)
                )
            
            # Analyze strategies
            with self.log_adapter.performance("strategy_analysis"):
                strategies = await self._analyze_strategies(text)
                self.logger.info(
                    "strategies_found",
                    document_id=document_id,
                    strategy_count=len(strategies)
                )
            
            self.logger.info(
                "document_processing_completed",
                document_id=document_id,
                user_id=user_id,
                strategies_extracted=len(strategies)
            )
            
            return strategies
            
        except Exception as e:
            self.logger.error(
                "document_processing_failed",
                document_id=document_id,
                user_id=user_id,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True
            )
            raise
    
    async def _validate_document(self, document_id: str):
        """Validate document with logging."""
        self.logger.debug("validating_document", document_id=document_id)
        # Implementation here
    
    async def _extract_text(self, document_id: str):
        """Extract text with logging."""
        self.logger.debug("extracting_text", document_id=document_id)
        # Implementation here
        return "Sample text content"
    
    async def _analyze_strategies(self, text: str):
        """Analyze strategies with logging."""
        self.logger.debug("analyzing_strategies", text_length=len(text))
        # Implementation here
        return ["strategy1", "strategy2"]


# API endpoint with decorator
@log_endpoint_performance
async def create_backtest_endpoint(backtest_request):
    """Example endpoint using the performance decorator."""
    logger.info(
        "backtest_creation_requested",
        strategy_id=backtest_request.strategy_id,
        start_date=backtest_request.start_date,
        end_date=backtest_request.end_date
    )
    
    # Endpoint implementation
    # The decorator automatically logs performance metrics
    
    return {"backtest_id": "bt_123", "status": "queued"}


# Configuration for different environments
def get_logging_config_examples():
    """Show how logging behaves in different environments."""
    
    # Development (debug=True):
    # - Colored console output
    # - Includes file names and line numbers
    # - All log levels shown
    # Example output:
    # 2024-01-15T10:30:45.123Z | INFO | app_name=FO Analytics | login_attempt | email=user@example.com | auth.py:75
    
    # Production (debug=False):
    # - JSON formatted output
    # - Structured for log aggregation
    # - Only INFO and above shown
    # Example output:
    # {"timestamp":"2024-01-15T10:30:45.123Z","level":"INFO","app_name":"FO Analytics","event":"login_attempt","email":"user@example.com"}
    
    pass


if __name__ == "__main__":
    # Run examples
    basic_logging_examples()
    structured_data_example()
    performance_logging_example()
    exception_logging_example()
    correlation_example()