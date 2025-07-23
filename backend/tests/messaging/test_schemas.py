"""Tests for messaging schemas."""

import pytest
from datetime import datetime
from uuid import uuid4

from messaging.schemas import (
    MessageStatus,
    BaseMessage,
    DocumentProcessingMessage,
    ProcessingResultMessage
)


class TestMessageStatus:
    """Test MessageStatus enum."""
    
    def test_status_values(self):
        """Test that all status values are defined."""
        assert MessageStatus.PENDING == "pending"
        assert MessageStatus.PROCESSING == "processing"
        assert MessageStatus.COMPLETED == "completed"
        assert MessageStatus.FAILED == "failed"
        assert MessageStatus.RETRYING == "retrying"


class TestBaseMessage:
    """Test BaseMessage schema."""
    
    def test_create_base_message(self):
        """Test creating a base message."""
        message_id = uuid4()
        correlation_id = uuid4()
        
        message = BaseMessage(
            message_id=message_id,
            correlation_id=correlation_id,
            metadata={"key": "value"}
        )
        
        assert message.message_id == message_id
        assert message.correlation_id == correlation_id
        assert message.retry_count == 0
        assert message.metadata == {"key": "value"}
        assert isinstance(message.timestamp, datetime)
    
    def test_base_message_defaults(self):
        """Test base message with defaults."""
        message = BaseMessage(message_id=uuid4())
        
        assert message.correlation_id is None
        assert message.retry_count == 0
        assert message.metadata == {}
        assert isinstance(message.timestamp, datetime)


class TestDocumentProcessingMessage:
    """Test DocumentProcessingMessage schema."""
    
    def test_create_processing_message(self):
        """Test creating a document processing message."""
        message_id = uuid4()
        document_id = uuid4()
        user_id = uuid4()
        
        message = DocumentProcessingMessage(
            message_id=message_id,
            document_id=document_id,
            user_id=user_id,
            file_key="user123/document456.pdf",
            filename="strategy.pdf",
            file_size=1048576,
            content_type="application/pdf",
            processing_type="full"
        )
        
        assert message.message_id == message_id
        assert message.document_id == document_id
        assert message.user_id == user_id
        assert message.file_key == "user123/document456.pdf"
        assert message.filename == "strategy.pdf"
        assert message.file_size == 1048576
        assert message.content_type == "application/pdf"
        assert message.processing_type == "full"
    
    def test_processing_message_defaults(self):
        """Test processing message with defaults."""
        message = DocumentProcessingMessage(
            message_id=uuid4(),
            document_id=uuid4(),
            user_id=uuid4(),
            file_key="test.pdf",
            filename="test.pdf",
            file_size=1000,
            content_type="application/pdf"
        )
        
        assert message.processing_type == "full"
        assert message.retry_count == 0
        assert message.correlation_id is None
    
    def test_processing_message_json_serialization(self):
        """Test JSON serialization of processing message."""
        message = DocumentProcessingMessage(
            message_id=uuid4(),
            document_id=uuid4(),
            user_id=uuid4(),
            file_key="test.pdf",
            filename="test.pdf",
            file_size=1000,
            content_type="application/pdf"
        )
        
        json_str = message.model_dump_json()
        assert isinstance(json_str, str)
        
        # Deserialize and verify
        parsed = DocumentProcessingMessage.model_validate_json(json_str)
        assert parsed.message_id == message.message_id
        assert parsed.document_id == message.document_id
        assert parsed.filename == message.filename


class TestProcessingResultMessage:
    """Test ProcessingResultMessage schema."""
    
    def test_create_success_result(self):
        """Test creating a successful processing result."""
        message_id = uuid4()
        document_id = uuid4()
        
        message = ProcessingResultMessage(
            message_id=message_id,
            document_id=document_id,
            status=MessageStatus.COMPLETED,
            result={
                "extracted_text": "Sample text",
                "strategies": ["Strategy 1", "Strategy 2"],
                "metadata": {"pages": 10}
            },
            processing_time_ms=5432
        )
        
        assert message.message_id == message_id
        assert message.document_id == document_id
        assert message.status == MessageStatus.COMPLETED
        assert message.result["strategies"] == ["Strategy 1", "Strategy 2"]
        assert message.processing_time_ms == 5432
        assert message.error is None
    
    def test_create_failure_result(self):
        """Test creating a failed processing result."""
        message = ProcessingResultMessage(
            message_id=uuid4(),
            document_id=uuid4(),
            status=MessageStatus.FAILED,
            error="Failed to parse document"
        )
        
        assert message.status == MessageStatus.FAILED
        assert message.error == "Failed to parse document"
        assert message.result is None
        assert message.processing_time_ms is None
    
    def test_result_message_validation(self):
        """Test result message validation."""
        with pytest.raises(ValueError):
            # Should fail without required fields
            ProcessingResultMessage(
                message_id=uuid4(),
                status=MessageStatus.COMPLETED
            )