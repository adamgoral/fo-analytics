"""Tests for message publisher."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import json
import aio_pika

from messaging.publisher import MessagePublisher
from messaging.schemas import DocumentProcessingMessage, MessageStatus
from core.config import settings


class TestMessagePublisher:
    """Test MessagePublisher class."""
    
    @pytest.fixture
    def mock_connection(self):
        """Create mock RabbitMQ connection."""
        mock = AsyncMock()
        mock.get_exchange = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_exchange(self):
        """Create mock exchange."""
        mock = AsyncMock()
        mock.publish = AsyncMock()
        return mock
    
    @pytest.mark.asyncio
    async def test_publish_document_processing_success(self, mock_connection, mock_exchange):
        """Test successful document processing message publishing."""
        mock_connection.get_exchange.return_value = mock_exchange
        
        with patch("messaging.publisher.get_rabbitmq_connection", return_value=mock_connection):
            publisher = MessagePublisher()
            
            document_id = uuid4()
            user_id = uuid4()
            
            message_id = await publisher.publish_document_processing(
                document_id=document_id,
                user_id=user_id,
                file_key="user123/doc456.pdf",
                filename="strategy.pdf",
                file_size=1048576,
                content_type="application/pdf",
                processing_type="full"
            )
            
            assert isinstance(message_id, uuid4().__class__)
            mock_exchange.publish.assert_called_once()
            
            # Verify message content
            call_args = mock_exchange.publish.call_args[0][0]
            assert isinstance(call_args, aio_pika.Message)
            assert call_args.content_type == "application/json"
            assert call_args.delivery_mode == aio_pika.DeliveryMode.PERSISTENT
            
            # Verify routing key
            assert mock_exchange.publish.call_args[1]["routing_key"] == "document.process"
    
    @pytest.mark.asyncio
    async def test_publish_document_processing_with_correlation_id(self, mock_connection, mock_exchange):
        """Test publishing with correlation ID."""
        mock_connection.get_exchange.return_value = mock_exchange
        
        with patch("messaging.publisher.get_rabbitmq_connection", return_value=mock_connection):
            publisher = MessagePublisher()
            
            correlation_id = uuid4()
            
            message_id = await publisher.publish_document_processing(
                document_id=uuid4(),
                user_id=uuid4(),
                file_key="test.pdf",
                filename="test.pdf",
                file_size=1000,
                content_type="application/pdf",
                correlation_id=correlation_id
            )
            
            # Verify correlation ID was set
            call_args = mock_exchange.publish.call_args[0][0]
            assert call_args.correlation_id == str(correlation_id)
    
    @pytest.mark.asyncio
    async def test_publish_document_processing_failure(self, mock_connection, mock_exchange):
        """Test handling of publishing failure."""
        mock_connection.get_exchange.return_value = mock_exchange
        mock_exchange.publish.side_effect = Exception("Publishing failed")
        
        with patch("messaging.publisher.get_rabbitmq_connection", return_value=mock_connection):
            publisher = MessagePublisher()
            
            with pytest.raises(Exception, match="Publishing failed"):
                await publisher.publish_document_processing(
                    document_id=uuid4(),
                    user_id=uuid4(),
                    file_key="test.pdf",
                    filename="test.pdf",
                    file_size=1000,
                    content_type="application/pdf"
                )
    
    @pytest.mark.asyncio
    async def test_publish_processing_result_success(self, mock_connection, mock_exchange):
        """Test publishing successful processing result."""
        mock_connection.get_exchange.return_value = mock_exchange
        
        with patch("messaging.publisher.get_rabbitmq_connection", return_value=mock_connection):
            publisher = MessagePublisher()
            
            document_id = uuid4()
            result = {
                "extracted_text": "Sample text",
                "strategies": ["Strategy 1"],
                "metadata": {"pages": 5}
            }
            
            message_id = await publisher.publish_processing_result(
                document_id=document_id,
                status=MessageStatus.COMPLETED,
                result=result,
                processing_time_ms=1234
            )
            
            assert isinstance(message_id, uuid4().__class__)
            mock_exchange.publish.assert_called_once()
            
            # Verify routing key for completed status
            assert mock_exchange.publish.call_args[1]["routing_key"] == "document.completed"
    
    @pytest.mark.asyncio
    async def test_publish_processing_result_failure(self, mock_connection, mock_exchange):
        """Test publishing failed processing result."""
        mock_connection.get_exchange.return_value = mock_exchange
        
        with patch("messaging.publisher.get_rabbitmq_connection", return_value=mock_connection):
            publisher = MessagePublisher()
            
            message_id = await publisher.publish_processing_result(
                document_id=uuid4(),
                status=MessageStatus.FAILED,
                error="Document parsing failed"
            )
            
            # Verify routing key for failed status
            assert mock_exchange.publish.call_args[1]["routing_key"] == "document.failed"
    
    @pytest.mark.asyncio
    async def test_publish_retry_under_max_retries(self, mock_connection, mock_exchange):
        """Test publishing retry message under max retries."""
        mock_connection.get_exchange.return_value = mock_exchange
        
        with patch("messaging.publisher.get_rabbitmq_connection", return_value=mock_connection):
            publisher = MessagePublisher()
            
            original_message = DocumentProcessingMessage(
                message_id=uuid4(),
                document_id=uuid4(),
                user_id=uuid4(),
                file_key="test.pdf",
                filename="test.pdf",
                file_size=1000,
                content_type="application/pdf",
                retry_count=1
            )
            
            message_id = await publisher.publish_retry(
                original_message=original_message,
                error_reason="Temporary failure"
            )
            
            assert isinstance(message_id, uuid4().__class__)
            assert original_message.retry_count == 2
            assert original_message.metadata["last_error"] == "Temporary failure"
            
            # Should route to process queue for retry
            assert mock_exchange.publish.call_args[1]["routing_key"] == "document.process"
    
    @pytest.mark.asyncio
    async def test_publish_retry_exceeds_max_retries(self, mock_connection, mock_exchange):
        """Test publishing retry message that exceeds max retries."""
        mock_connection.get_exchange.return_value = mock_exchange
        
        with patch("messaging.publisher.get_rabbitmq_connection", return_value=mock_connection):
            publisher = MessagePublisher()
            
            original_message = DocumentProcessingMessage(
                message_id=uuid4(),
                document_id=uuid4(),
                user_id=uuid4(),
                file_key="test.pdf",
                filename="test.pdf",
                file_size=1000,
                content_type="application/pdf",
                retry_count=settings.rabbitmq_max_retries
            )
            
            message_id = await publisher.publish_retry(
                original_message=original_message,
                error_reason="Permanent failure"
            )
            
            # Should route to failed queue (DLQ)
            assert mock_exchange.publish.call_args[1]["routing_key"] == "document.failed"
    
    @pytest.mark.asyncio
    async def test_publish_retry_with_exponential_backoff(self, mock_connection, mock_exchange):
        """Test retry delay calculation."""
        mock_connection.get_exchange.return_value = mock_exchange
        
        with patch("messaging.publisher.get_rabbitmq_connection", return_value=mock_connection):
            publisher = MessagePublisher()
            
            original_message = DocumentProcessingMessage(
                message_id=uuid4(),
                document_id=uuid4(),
                user_id=uuid4(),
                file_key="test.pdf",
                filename="test.pdf",
                file_size=1000,
                content_type="application/pdf",
                retry_count=2
            )
            
            await publisher.publish_retry(
                original_message=original_message,
                error_reason="Retry test"
            )
            
            # Verify exponential backoff calculation
            # retry_count=3 -> delay = 1000 * 2^2 = 4000ms
            assert original_message.metadata["retry_delay_ms"] == 4000
            
            # Verify delay header is set
            call_args = mock_exchange.publish.call_args[0][0]
            assert call_args.headers["x-delay"] == 4000