"""Message publisher for RabbitMQ."""

import json
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

import aio_pika
import structlog

from core.config import settings
from .connection import get_rabbitmq_connection
from .schemas import DocumentProcessingMessage, ProcessingResultMessage

logger = structlog.get_logger(__name__)


class MessagePublisher:
    """Publishes messages to RabbitMQ queues."""
    
    def __init__(self):
        self._connection = None
        
    async def _ensure_connection(self):
        """Ensure we have an active connection."""
        if not self._connection:
            self._connection = await get_rabbitmq_connection()
            
    async def publish_document_processing(
        self,
        document_id: UUID,
        user_id: UUID,
        file_key: str,
        filename: str,
        file_size: int,
        content_type: str,
        processing_type: str = "full",
        correlation_id: Optional[UUID] = None
    ) -> UUID:
        """
        Publish a document processing message.
        
        Args:
            document_id: ID of the document to process
            user_id: ID of the user who uploaded the document
            file_key: S3/MinIO object key
            filename: Original filename
            file_size: File size in bytes
            content_type: MIME type
            processing_type: Type of processing (full, parse_only, extract_only)
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            Message ID
        """
        await self._ensure_connection()
        
        message_id = uuid4()
        message = DocumentProcessingMessage(
            message_id=message_id,
            correlation_id=correlation_id,
            document_id=document_id,
            user_id=user_id,
            file_key=file_key,
            filename=filename,
            file_size=file_size,
            content_type=content_type,
            processing_type=processing_type
        )
        
        try:
            exchange = await self._connection.get_exchange()
            
            # Convert to JSON and publish
            await exchange.publish(
                aio_pika.Message(
                    body=message.model_dump_json().encode(),
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    message_id=str(message_id),
                    correlation_id=str(correlation_id) if correlation_id else None,
                ),
                routing_key="document.process"
            )
            
            logger.info(
                "Published document processing message",
                message_id=str(message_id),
                document_id=str(document_id),
                processing_type=processing_type
            )
            
            return message_id
            
        except Exception as e:
            logger.error(
                "Failed to publish document processing message",
                error=str(e),
                document_id=str(document_id)
            )
            raise
            
    async def publish_processing_result(
        self,
        document_id: UUID,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        processing_time_ms: Optional[int] = None,
        correlation_id: Optional[UUID] = None
    ) -> UUID:
        """
        Publish a processing result message.
        
        Args:
            document_id: ID of the processed document
            status: Processing status
            result: Processing results (if successful)
            error: Error message (if failed)
            processing_time_ms: Processing time in milliseconds
            correlation_id: Optional correlation ID
            
        Returns:
            Message ID
        """
        await self._ensure_connection()
        
        message_id = uuid4()
        message = ProcessingResultMessage(
            message_id=message_id,
            correlation_id=correlation_id,
            document_id=document_id,
            status=status,
            result=result,
            error=error,
            processing_time_ms=processing_time_ms
        )
        
        try:
            exchange = await self._connection.get_exchange()
            
            # Determine routing key based on status
            routing_key = "document.completed" if status == "completed" else "document.failed"
            
            await exchange.publish(
                aio_pika.Message(
                    body=message.model_dump_json().encode(),
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    message_id=str(message_id),
                    correlation_id=str(correlation_id) if correlation_id else None,
                ),
                routing_key=routing_key
            )
            
            logger.info(
                "Published processing result message",
                message_id=str(message_id),
                document_id=str(document_id),
                status=status
            )
            
            return message_id
            
        except Exception as e:
            logger.error(
                "Failed to publish processing result message",
                error=str(e),
                document_id=str(document_id)
            )
            raise
            
    async def publish_retry(
        self,
        original_message: DocumentProcessingMessage,
        error_reason: str
    ) -> UUID:
        """
        Publish a retry message for failed processing.
        
        Args:
            original_message: The original message to retry
            error_reason: Reason for the retry
            
        Returns:
            New message ID
        """
        # Increment retry count
        original_message.retry_count += 1
        original_message.metadata["last_error"] = error_reason
        original_message.metadata["retry_at"] = str(original_message.timestamp)
        
        # Check if we've exceeded max retries
        if original_message.retry_count > settings.rabbitmq_max_retries:
            # Send to dead letter queue
            logger.warning(
                "Max retries exceeded, sending to DLQ",
                document_id=str(original_message.document_id),
                retry_count=original_message.retry_count
            )
            routing_key = "document.failed"
        else:
            # Retry with exponential backoff
            delay_ms = 1000 * (2 ** (original_message.retry_count - 1))
            original_message.metadata["retry_delay_ms"] = delay_ms
            routing_key = "document.process"
            
        await self._ensure_connection()
        
        try:
            exchange = await self._connection.get_exchange()
            
            # Create new message with updated retry info
            new_message_id = uuid4()
            original_message.message_id = new_message_id
            
            await exchange.publish(
                aio_pika.Message(
                    body=original_message.model_dump_json().encode(),
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    message_id=str(new_message_id),
                    correlation_id=str(original_message.correlation_id),
                    # Add delay for retry
                    headers={"x-delay": original_message.metadata.get("retry_delay_ms", 0)}
                ),
                routing_key=routing_key
            )
            
            logger.info(
                "Published retry message",
                message_id=str(new_message_id),
                document_id=str(original_message.document_id),
                retry_count=original_message.retry_count,
                routing_key=routing_key
            )
            
            return new_message_id
            
        except Exception as e:
            logger.error(
                "Failed to publish retry message",
                error=str(e),
                document_id=str(original_message.document_id)
            )
            raise