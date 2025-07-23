"""Tests for WebSocket notifications in document processing consumer."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import json

from messaging.consumer import DocumentProcessingConsumer
from messaging.schemas import DocumentProcessingMessage
from api.websockets import notifier


@pytest.mark.asyncio
class TestConsumerWebSocketNotifications:
    """Test WebSocket notifications in document processing consumer."""
    
    @pytest.fixture
    def mock_services(self, monkeypatch):
        """Mock all external services."""
        # Mock storage service
        mock_storage = MagicMock()
        mock_storage.download_file = AsyncMock(return_value=b"file content")
        monkeypatch.setattr(
            "messaging.consumer.StorageService",
            lambda: mock_storage
        )
        
        # Mock parser service
        mock_parser = MagicMock()
        mock_parsed_doc = MagicMock()
        mock_parsed_doc.text = "Extracted document text"
        mock_parsed_doc.metadata = {"pages": 10}
        mock_parsed_doc.pages = ["page1", "page2"]
        mock_parser.parse_document = AsyncMock(return_value=mock_parsed_doc)
        monkeypatch.setattr(
            "messaging.consumer.DocumentParserService",
            lambda: mock_parser
        )
        
        # Mock LLM service
        mock_llm = MagicMock()
        mock_llm.extract_strategies = AsyncMock(return_value=[
            {"name": "Strategy 1", "description": "Test strategy 1"},
            {"name": "Strategy 2", "description": "Test strategy 2"}
        ])
        monkeypatch.setattr(
            "messaging.consumer.LLMService",
            lambda: mock_llm
        )
        
        # Mock notifier
        mock_notifier = MagicMock()
        mock_notifier.document_processing_started = AsyncMock()
        mock_notifier.document_processing_progress = AsyncMock()
        mock_notifier.document_processing_completed = AsyncMock()
        mock_notifier.document_processing_failed = AsyncMock()
        mock_notifier.strategy_extracted = AsyncMock()
        monkeypatch.setattr("messaging.consumer.notifier", mock_notifier)
        
        return {
            "storage": mock_storage,
            "parser": mock_parser,
            "llm": mock_llm,
            "notifier": mock_notifier
        }
    
    @pytest.fixture
    def sample_message(self):
        """Create a sample document processing message."""
        return DocumentProcessingMessage(
            message_id=uuid4(),
            document_id=uuid4(),
            user_id=uuid4(),
            file_key="test/document.pdf",
            filename="document.pdf",
            file_size=1024,
            content_type="application/pdf",
            processing_type="full"
        )
    
    async def test_processing_started_notification(self, mock_services, sample_message):
        """Test that processing started notification is sent."""
        consumer = DocumentProcessingConsumer()
        
        # Mock database operations
        with patch("messaging.consumer.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_repo = MagicMock()
            mock_repo.update = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]
            
            with patch("messaging.consumer.DocumentRepository", return_value=mock_repo):
                # Process message (will fail after notifications, but that's ok)
                try:
                    await consumer._process_message(MagicMock(
                        body=sample_message.model_dump_json().encode(),
                        ack=AsyncMock()
                    ))
                except:
                    pass
        
        # Verify notification was sent
        mock_services["notifier"].document_processing_started.assert_called_once_with(
            user_id=str(sample_message.user_id),
            document_id=str(sample_message.document_id)
        )
    
    async def test_parse_progress_notifications(self, mock_services, sample_message):
        """Test that parsing progress notifications are sent."""
        consumer = DocumentProcessingConsumer()
        
        # Call parse document directly
        await consumer._parse_document(sample_message)
        
        # Verify progress notifications
        calls = mock_services["notifier"].document_processing_progress.call_args_list
        assert len(calls) >= 2
        
        # Check first progress notification
        assert calls[0][1]["user_id"] == str(sample_message.user_id)
        assert calls[0][1]["document_id"] == str(sample_message.document_id)
        assert calls[0][1]["progress"] == 0.2
        assert "download" in calls[0][1]["message"].lower()
        
        # Check second progress notification
        assert calls[1][1]["progress"] == 0.4
        assert "parsing" in calls[1][1]["message"].lower()
    
    async def test_extract_progress_notifications(self, mock_services, sample_message):
        """Test that extraction progress notifications are sent."""
        consumer = DocumentProcessingConsumer()
        
        # Mock database operations
        with patch("messaging.consumer.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_repo = MagicMock()
            mock_document = MagicMock()
            mock_document.extracted_text = "Document text"
            mock_repo.get = AsyncMock(return_value=mock_document)
            mock_get_db.return_value.__aiter__.return_value = [mock_db]
            
            with patch("messaging.consumer.DocumentRepository", return_value=mock_repo):
                # Call extract strategies
                await consumer._extract_strategies(sample_message)
        
        # Verify progress notifications
        calls = mock_services["notifier"].document_processing_progress.call_args_list
        assert len(calls) >= 2
        
        # Check retrieving text notification
        assert calls[0][1]["progress"] == 0.6
        assert "retrieving" in calls[0][1]["message"].lower()
        
        # Check analyzing notification
        assert calls[1][1]["progress"] == 0.8
        assert "analyzing" in calls[1][1]["message"].lower()
    
    async def test_strategy_extracted_notifications(self, mock_services, sample_message):
        """Test that strategy extracted notifications are sent."""
        consumer = DocumentProcessingConsumer()
        
        # Mock database operations
        with patch("messaging.consumer.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_repo = MagicMock()
            mock_document = MagicMock()
            mock_document.extracted_text = "Document text"
            mock_repo.get = AsyncMock(return_value=mock_document)
            mock_get_db.return_value.__aiter__.return_value = [mock_db]
            
            with patch("messaging.consumer.DocumentRepository", return_value=mock_repo):
                # Call extract strategies
                result = await consumer._extract_strategies(sample_message)
        
        # Verify strategy notifications
        calls = mock_services["notifier"].strategy_extracted.call_args_list
        assert len(calls) == 2  # Two strategies in mock
        
        # Check first strategy notification
        assert calls[0][1]["user_id"] == str(sample_message.user_id)
        assert calls[0][1]["document_id"] == str(sample_message.document_id)
        assert calls[0][1]["strategy_name"] == "Strategy 1"
        
        # Check second strategy notification
        assert calls[1][1]["strategy_name"] == "Strategy 2"
    
    async def test_processing_completed_notification(self, mock_services, sample_message):
        """Test that processing completed notification is sent."""
        consumer = DocumentProcessingConsumer()
        
        # Mock everything needed for full processing
        with patch("messaging.consumer.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_repo = MagicMock()
            mock_repo.update = AsyncMock()
            mock_repo.get = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]
            
            with patch("messaging.consumer.DocumentRepository", return_value=mock_repo):
                with patch.object(consumer._publisher, "publish_processing_result", new_callable=AsyncMock):
                    # Process message
                    mock_message = MagicMock()
                    mock_message.body = sample_message.model_dump_json().encode()
                    mock_message.ack = AsyncMock()
                    
                    await consumer._process_message(mock_message)
        
        # Verify completed notification
        mock_services["notifier"].document_processing_completed.assert_called_once()
        call_args = mock_services["notifier"].document_processing_completed.call_args[1]
        assert call_args["user_id"] == str(sample_message.user_id)
        assert call_args["document_id"] == str(sample_message.document_id)
        assert call_args["strategies_count"] == 2  # From mock LLM service
    
    async def test_processing_failed_notification(self, mock_services, sample_message):
        """Test that processing failed notification is sent."""
        consumer = DocumentProcessingConsumer()
        
        # Make parser fail
        mock_services["parser"].parse_document.side_effect = Exception("Parse error")
        
        # Mock database operations
        with patch("messaging.consumer.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_repo = MagicMock()
            mock_repo.update = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]
            
            with patch("messaging.consumer.DocumentRepository", return_value=mock_repo):
                with patch.object(consumer._publisher, "publish_retry", new_callable=AsyncMock):
                    # Process message
                    mock_message = MagicMock()
                    mock_message.body = sample_message.model_dump_json().encode()
                    mock_message.ack = AsyncMock()
                    mock_message.reject = AsyncMock()
                    
                    await consumer._process_message(mock_message)
        
        # Verify failed notification
        mock_services["notifier"].document_processing_failed.assert_called_once()
        call_args = mock_services["notifier"].document_processing_failed.call_args[1]
        assert call_args["user_id"] == str(sample_message.user_id)
        assert call_args["document_id"] == str(sample_message.document_id)
        assert "Parse error" in call_args["error"]
    
    async def test_full_processing_notifications_flow(self, mock_services, sample_message):
        """Test the complete flow of notifications during full processing."""
        consumer = DocumentProcessingConsumer()
        sample_message.processing_type = "full"
        
        # Track all notifications in order
        all_notifications = []
        
        def track_notification(method_name):
            def side_effect(*args, **kwargs):
                all_notifications.append((method_name, kwargs))
                return AsyncMock()(*args, **kwargs)
            return side_effect
        
        # Set up tracking for all notification methods
        for method in ["document_processing_started", "document_processing_progress",
                      "document_processing_completed", "strategy_extracted"]:
            getattr(mock_services["notifier"], method).side_effect = track_notification(method)
        
        # Mock database operations
        with patch("messaging.consumer.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_repo = MagicMock()
            mock_repo.update = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]
            
            with patch("messaging.consumer.DocumentRepository", return_value=mock_repo):
                with patch.object(consumer._publisher, "publish_processing_result", new_callable=AsyncMock):
                    # Process message
                    mock_message = MagicMock()
                    mock_message.body = sample_message.model_dump_json().encode()
                    mock_message.ack = AsyncMock()
                    
                    await consumer._process_message(mock_message)
        
        # Verify notification order
        notification_types = [n[0] for n in all_notifications]
        
        # Should start with processing started
        assert notification_types[0] == "document_processing_started"
        
        # Should have progress notifications
        progress_notifications = [n for n in all_notifications if n[0] == "document_processing_progress"]
        assert len(progress_notifications) >= 4  # At least 4 progress updates
        
        # Should have strategy notifications
        strategy_notifications = [n for n in all_notifications if n[0] == "strategy_extracted"]
        assert len(strategy_notifications) == 2  # Two strategies
        
        # Should end with completed
        assert notification_types[-1] == "document_processing_completed"
        
        # All notifications should have correct user_id and document_id
        for _, kwargs in all_notifications:
            assert kwargs.get("user_id") == str(sample_message.user_id)
            assert kwargs.get("document_id") == str(sample_message.document_id)