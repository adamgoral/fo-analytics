"""Tests for document processing consumer."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4
import json
import time
import aio_pika

from messaging.consumer import DocumentProcessingConsumer
from messaging.schemas import DocumentProcessingMessage, MessageStatus
from models.document import DocumentStatus


class TestDocumentProcessingConsumer:
    """Test DocumentProcessingConsumer class."""
    
    @pytest.fixture
    def mock_connection(self):
        """Create mock RabbitMQ connection."""
        mock = AsyncMock()
        mock.get_channel = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_channel(self):
        """Create mock channel."""
        mock = AsyncMock()
        mock.get_queue = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_storage_service(self):
        """Create mock storage service."""
        mock = AsyncMock()
        mock.download_file = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_parser_service(self):
        """Create mock parser service."""
        mock = AsyncMock()
        mock.parse_document = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create mock LLM service."""
        mock = AsyncMock()
        mock.extract_strategies = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_publisher(self):
        """Create mock message publisher."""
        mock = AsyncMock()
        mock.publish_processing_result = AsyncMock()
        mock.publish_retry = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_document_repo(self):
        """Create mock document repository."""
        mock = AsyncMock()
        mock.get = AsyncMock()
        mock.update = AsyncMock()
        return mock
    
    @pytest.fixture
    def sample_message_data(self):
        """Create sample document processing message data."""
        return DocumentProcessingMessage(
            message_id=uuid4(),
            document_id=uuid4(),
            user_id=uuid4(),
            file_key="user123/doc456.pdf",
            filename="strategy.pdf",
            file_size=1048576,
            content_type="application/pdf",
            processing_type="full"
        )
    
    @pytest.fixture
    def mock_incoming_message(self, sample_message_data):
        """Create mock incoming message."""
        mock = AsyncMock()
        mock.body = sample_message_data.model_dump_json().encode()
        mock.message_id = str(sample_message_data.message_id)
        mock.ack = AsyncMock()
        mock.reject = AsyncMock()
        return mock
    
    @pytest.mark.asyncio
    async def test_consumer_initialization(self):
        """Test consumer initialization."""
        consumer = DocumentProcessingConsumer()
        
        assert consumer._running is False
        assert consumer._connection is None
        assert consumer._publisher is not None
        assert consumer._storage_service is not None
        assert consumer._parser_service is not None
        assert consumer._llm_service is not None
    
    @pytest.mark.asyncio
    async def test_process_message_parse_only(
        self,
        mock_storage_service,
        mock_parser_service,
        mock_publisher,
        mock_document_repo,
        mock_incoming_message
    ):
        """Test processing message with parse_only type."""
        # Setup
        consumer = DocumentProcessingConsumer()
        consumer._storage_service = mock_storage_service
        consumer._parser_service = mock_parser_service
        consumer._publisher = mock_publisher
        
        # Mock responses
        mock_storage_service.download_file.return_value = b"file content"
        mock_parser_service.parse_document.return_value = MagicMock(
            text="Extracted text",
            metadata={"pages": 5},
            pages=["page1", "page2", "page3", "page4", "page5"]
        )
        
        # Update message type
        message_data = DocumentProcessingMessage.model_validate_json(mock_incoming_message.body)
        message_data.processing_type = "parse_only"
        mock_incoming_message.body = message_data.model_dump_json().encode()
        
        with patch("messaging.consumer.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]
            mock_db.commit = AsyncMock()
            
            with patch("messaging.consumer.DocumentRepository", return_value=mock_document_repo):
                await consumer._process_message(mock_incoming_message)
        
        # Verify storage download was called
        mock_storage_service.download_file.assert_called_once_with(message_data.file_key)
        
        # Verify parser was called
        mock_parser_service.parse_document.assert_called_once()
        
        # Verify result was published
        mock_publisher.publish_processing_result.assert_called_once()
        result_call = mock_publisher.publish_processing_result.call_args
        assert result_call[1]["status"] == MessageStatus.COMPLETED
        assert "extracted_text" in result_call[1]["result"]
        assert result_call[1]["result"]["pages"] == 5
        
        # Verify message was acknowledged
        mock_incoming_message.ack.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_extract_only(
        self,
        mock_llm_service,
        mock_publisher,
        mock_document_repo,
        mock_incoming_message
    ):
        """Test processing message with extract_only type."""
        # Setup
        consumer = DocumentProcessingConsumer()
        consumer._llm_service = mock_llm_service
        consumer._publisher = mock_publisher
        
        # Mock document with extracted text
        mock_document = MagicMock()
        mock_document.extracted_text = "Sample document text for strategy extraction"
        mock_document_repo.get.return_value = mock_document
        
        # Mock LLM response
        mock_llm_service.extract_strategies.return_value = [
            {"name": "Strategy 1", "description": "Buy low, sell high"},
            {"name": "Strategy 2", "description": "Diversify portfolio"}
        ]
        
        # Update message type
        message_data = DocumentProcessingMessage.model_validate_json(mock_incoming_message.body)
        message_data.processing_type = "extract_only"
        mock_incoming_message.body = message_data.model_dump_json().encode()
        
        with patch("messaging.consumer.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]
            mock_db.commit = AsyncMock()
            
            with patch("messaging.consumer.DocumentRepository", return_value=mock_document_repo):
                await consumer._process_message(mock_incoming_message)
        
        # Verify LLM was called with document text
        mock_llm_service.extract_strategies.assert_called_once_with(mock_document.extracted_text)
        
        # Verify result was published
        mock_publisher.publish_processing_result.assert_called_once()
        result_call = mock_publisher.publish_processing_result.call_args
        assert result_call[1]["status"] == MessageStatus.COMPLETED
        assert result_call[1]["result"]["strategy_count"] == 2
        
        # Verify message was acknowledged
        mock_incoming_message.ack.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_full_processing(
        self,
        mock_storage_service,
        mock_parser_service,
        mock_llm_service,
        mock_publisher,
        mock_document_repo,
        mock_incoming_message
    ):
        """Test full document processing."""
        # Setup
        consumer = DocumentProcessingConsumer()
        consumer._storage_service = mock_storage_service
        consumer._parser_service = mock_parser_service
        consumer._llm_service = mock_llm_service
        consumer._publisher = mock_publisher
        
        # Mock responses
        mock_storage_service.download_file.return_value = b"file content"
        mock_parser_service.parse_document.return_value = MagicMock(
            text="Document text",
            metadata={"title": "Strategy Doc"},
            pages=["page1"]
        )
        mock_llm_service.extract_strategies.return_value = [
            {"name": "Growth Strategy", "allocation": "60%"}
        ]
        
        with patch("messaging.consumer.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]
            mock_db.commit = AsyncMock()
            
            with patch("messaging.consumer.DocumentRepository", return_value=mock_document_repo):
                await consumer._process_message(mock_incoming_message)
        
        # Verify all services were called
        mock_storage_service.download_file.assert_called_once()
        mock_parser_service.parse_document.assert_called_once()
        mock_llm_service.extract_strategies.assert_called_once()
        
        # Verify document was updated
        assert mock_document_repo.update.call_count >= 2  # status updates
        
        # Verify result includes both parsing and extraction
        result_call = mock_publisher.publish_processing_result.call_args
        assert "extracted_text" in result_call[1]["result"]
        assert "strategies" in result_call[1]["result"]
        
        mock_incoming_message.ack.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_failure_with_retry(
        self,
        mock_storage_service,
        mock_publisher,
        mock_document_repo,
        mock_incoming_message,
        sample_message_data
    ):
        """Test message processing failure with retry."""
        # Setup
        consumer = DocumentProcessingConsumer()
        consumer._storage_service = mock_storage_service
        consumer._publisher = mock_publisher
        
        # Mock storage failure
        mock_storage_service.download_file.side_effect = Exception("Storage unavailable")
        
        with patch("messaging.consumer.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]
            mock_db.commit = AsyncMock()
            
            with patch("messaging.consumer.DocumentRepository", return_value=mock_document_repo):
                await consumer._process_message(mock_incoming_message)
        
        # Verify retry was published
        mock_publisher.publish_retry.assert_called_once()
        retry_call = mock_publisher.publish_retry.call_args
        assert "Storage unavailable" in retry_call[0][1]
        
        # Verify original message was acknowledged
        mock_incoming_message.ack.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_max_retries_exceeded(
        self,
        mock_storage_service,
        mock_publisher,
        mock_document_repo,
        mock_incoming_message
    ):
        """Test message processing when max retries exceeded."""
        # Setup
        consumer = DocumentProcessingConsumer()
        consumer._storage_service = mock_storage_service
        consumer._publisher = mock_publisher
        
        # Update message with max retries
        message_data = DocumentProcessingMessage.model_validate_json(mock_incoming_message.body)
        message_data.retry_count = 3  # Max retries
        mock_incoming_message.body = message_data.model_dump_json().encode()
        
        # Mock storage failure
        mock_storage_service.download_file.side_effect = Exception("Permanent failure")
        
        with patch("messaging.consumer.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]
            mock_db.commit = AsyncMock()
            
            with patch("messaging.consumer.DocumentRepository", return_value=mock_document_repo):
                await consumer._process_message(mock_incoming_message)
        
        # Verify message was rejected (sent to DLQ)
        mock_incoming_message.reject.assert_called_once_with(requeue=False)
        
        # Verify failure result was published
        mock_publisher.publish_processing_result.assert_called_once()
        result_call = mock_publisher.publish_processing_result.call_args
        assert result_call[1]["status"] == MessageStatus.FAILED
        assert "Max retries exceeded" in result_call[1]["error"]
    
    @pytest.mark.asyncio
    async def test_process_message_invalid_json(self, mock_incoming_message):
        """Test handling of invalid message JSON."""
        consumer = DocumentProcessingConsumer()
        
        # Set invalid JSON
        mock_incoming_message.body = b"invalid json"
        
        await consumer._process_message(mock_incoming_message)
        
        # Should reject without requeue
        mock_incoming_message.reject.assert_called_once_with(requeue=False)
    
    @pytest.mark.asyncio
    async def test_stop_consumer(self):
        """Test stopping the consumer."""
        consumer = DocumentProcessingConsumer()
        consumer._running = True
        
        await consumer.stop()
        
        assert consumer._running is False