"""Message schemas for RabbitMQ communication."""

from datetime import datetime
from enum import StrEnum, auto
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MessageStatus(StrEnum):
    """Status of a message in the processing pipeline."""
    
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    RETRYING = auto()


class BaseMessage(BaseModel):
    """Base message schema with common fields."""
    
    message_id: UUID = Field(description="Unique message identifier")
    correlation_id: Optional[UUID] = Field(default=None, description="Correlation ID for tracking related messages")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message creation timestamp")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DocumentProcessingMessage(BaseMessage):
    """Message schema for document processing tasks."""
    
    document_id: UUID = Field(description="Document ID to process")
    user_id: UUID = Field(description="User who uploaded the document")
    file_key: str = Field(description="S3/MinIO object key")
    filename: str = Field(description="Original filename")
    file_size: int = Field(description="File size in bytes")
    content_type: str = Field(description="MIME type of the document")
    processing_type: str = Field(default="full", description="Type of processing: full, parse_only, extract_only")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "123e4567-e89b-12d3-a456-426614174000",
                "document_id": "456e7890-e89b-12d3-a456-426614174000",
                "user_id": "789e0123-e89b-12d3-a456-426614174000",
                "file_key": "789e0123-e89b-12d3-a456-426614174000/doc_456e7890.pdf",
                "filename": "investment_strategy.pdf",
                "file_size": 1048576,
                "content_type": "application/pdf",
                "processing_type": "full",
                "retry_count": 0,
                "timestamp": "2025-07-23T10:30:00Z"
            }
        }


class ProcessingResultMessage(BaseMessage):
    """Message schema for processing results."""
    
    document_id: UUID = Field(description="Document ID that was processed")
    status: MessageStatus = Field(description="Processing status")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Processing results")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "123e4567-e89b-12d3-a456-426614174001",
                "document_id": "456e7890-e89b-12d3-a456-426614174000",
                "status": "completed",
                "result": {
                    "extracted_text": "...",
                    "strategies": ["Strategy 1", "Strategy 2"],
                    "metadata": {"pages": 10}
                },
                "processing_time_ms": 5432
            }
        }


class BacktestExecutionMessage(BaseMessage):
    """Message schema for backtest execution tasks."""
    
    backtest_id: int = Field(description="Backtest ID to execute")
    user_id: UUID = Field(description="User who created the backtest")
    strategy_id: int = Field(description="Strategy ID to backtest")
    strategy_name: str = Field(description="Strategy name")
    strategy_code: str = Field(description="Strategy code to execute")
    parameters: Dict[str, Any] = Field(description="Backtest parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "123e4567-e89b-12d3-a456-426614174002",
                "backtest_id": 1,
                "user_id": "789e0123-e89b-12d3-a456-426614174000",
                "strategy_id": 1,
                "strategy_name": "Momentum Strategy",
                "strategy_code": "def backtest(): ...",
                "parameters": {
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "initial_capital": 100000,
                    "max_positions": 10
                }
            }
        }