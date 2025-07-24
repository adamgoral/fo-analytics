"""Tests for document API logging functionality."""

import pytest
import tempfile
from io import BytesIO
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from src.models.user import User
from src.models.document import Document, DocumentStatus, DocumentType


@pytest.mark.asyncio
class TestDocumentsLogging:
    """Test document API logging functionality."""
    
    @pytest.fixture
    async def authenticated_client(self, async_client: AsyncClient, async_session: AsyncSession):
        """Create an authenticated client with a test user."""
        # Register a test user
        user_data = {
            "name": "Log Test User",
            "email": "logtest@example.com",
            "password": "testPassword123!",
            "role": "viewer"
        }
        
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        # Login to get access token
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        
        # Get the user from database for reference
        from src.repositories.user import UserRepository
        user_repo = UserRepository(async_session)
        user = await user_repo.get_by_email(user_data["email"])
        
        # Create a client with auth headers
        headers = {"Authorization": f"Bearer {access_token}"}
        
        yield async_client, user, headers
    
    async def test_upload_document_message_publisher_error_logging(self, authenticated_client):
        """Test that errors in message publishing are properly logged."""
        async_client, user, headers = authenticated_client
        
        # Create a test file
        file_content = b"Test document content for logging"
        file = BytesIO(file_content)
        
        # Mock storage service to succeed
        with patch('src.api.documents.storage_service.upload') as mock_upload:
            mock_upload.return_value = "test-key"
            
            # Mock document parser to succeed
            with patch('src.api.documents.DocumentParserService') as mock_parser:
                mock_parser_instance = AsyncMock()
                mock_parser_instance.get_basic_info = AsyncMock(return_value={
                    "pages": 1,
                    "file_size": len(file_content),
                    "content_type": "application/pdf"
                })
                mock_parser.return_value = mock_parser_instance
                
                # Mock message publisher to fail
                with patch('src.api.documents.MessagePublisher') as mock_publisher_class:
                    mock_publisher = AsyncMock()
                    mock_publisher.publish_document_processing = AsyncMock(
                        side_effect=Exception("RabbitMQ connection failed")
                    )
                    mock_publisher_class.return_value = mock_publisher
                    
                    # Mock logger to capture log calls
                    with patch('src.api.documents.logger') as mock_logger:
                        # Upload document
                        response = await async_client.post(
                            "/api/v1/documents/upload",
                            headers=headers,
                            files={"file": ("test.pdf", file, "application/pdf")}
                        )
                        
                        # Should succeed despite message publisher error
                        assert response.status_code == 201
                        
                        # Verify error was logged with proper context
                        mock_logger.error.assert_called_once()
                        call_args = mock_logger.error.call_args
                        
                        # Check log message
                        assert call_args[0][0] == "Failed to publish document processing message"
                        
                        # Check log context
                        kwargs = call_args[1]
                        assert "document_id" in kwargs
                        assert "user_id" in kwargs
                        assert kwargs["user_id"] == str(user.id)
                        assert kwargs["filename"] == "test.pdf"
                        assert kwargs["error"] == "RabbitMQ connection failed"
                        assert kwargs["exc_info"] is True
    
    async def test_upload_document_websocket_notification_continues_after_publisher_error(self, authenticated_client):
        """Test that WebSocket notifications still work after message publisher error."""
        async_client, user, headers = authenticated_client
        
        # Create a test file
        file_content = b"Test document content"
        file = BytesIO(file_content)
        
        # Mock all dependencies
        with patch('src.api.documents.storage_service.upload') as mock_upload:
            mock_upload.return_value = "test-key"
            
            with patch('src.api.documents.DocumentParserService') as mock_parser:
                mock_parser_instance = AsyncMock()
                mock_parser_instance.get_basic_info = AsyncMock(return_value={
                    "pages": 1,
                    "file_size": len(file_content),
                    "content_type": "application/pdf"
                })
                mock_parser.return_value = mock_parser_instance
                
                # Mock message publisher to fail
                with patch('src.api.documents.MessagePublisher') as mock_publisher_class:
                    mock_publisher = AsyncMock()
                    mock_publisher.publish_document_processing = AsyncMock(
                        side_effect=Exception("Publisher error")
                    )
                    mock_publisher_class.return_value = mock_publisher
                    
                    # Mock WebSocket notifier
                    with patch('src.api.documents.notifier') as mock_notifier:
                        mock_notifier.document_upload_completed = AsyncMock()
                        
                        # Upload document
                        response = await async_client.post(
                            "/api/v1/documents/upload",
                            headers=headers,
                            files={"file": ("test.pdf", file, "application/pdf")}
                        )
                        
                        # Should succeed
                        assert response.status_code == 201
                        
                        # Verify WebSocket notification was still sent
                        mock_notifier.document_upload_completed.assert_called_once()
                        call_args = mock_notifier.document_upload_completed.call_args[1]
                        assert call_args["user_id"] == str(user.id)
                        assert call_args["filename"] == "test.pdf"
    
    async def test_upload_document_logging_preserves_error_details(self, authenticated_client):
        """Test that logging preserves full error details including stack trace."""
        async_client, user, headers = authenticated_client
        
        # Create a test file
        file_content = b"Test document"
        file = BytesIO(file_content)
        
        # Create a specific error to test
        test_error = ConnectionError("RabbitMQ server unreachable at localhost:5672")
        
        with patch('src.api.documents.storage_service.upload', return_value="test-key"):
            with patch('src.api.documents.DocumentParserService') as mock_parser:
                mock_parser_instance = AsyncMock()
                mock_parser_instance.get_basic_info = AsyncMock(return_value={
                    "pages": 1,
                    "file_size": len(file_content),
                    "content_type": "application/pdf"
                })
                mock_parser.return_value = mock_parser_instance
                
                with patch('src.api.documents.MessagePublisher') as mock_publisher_class:
                    mock_publisher = AsyncMock()
                    mock_publisher.publish_document_processing = AsyncMock(side_effect=test_error)
                    mock_publisher_class.return_value = mock_publisher
                    
                    # Capture actual logger calls
                    with patch('src.api.documents.logger.error') as mock_error:
                        # Upload document
                        response = await async_client.post(
                            "/api/v1/documents/upload",
                            headers=headers,
                            files={"file": ("test.pdf", file, "application/pdf")}
                        )
                        
                        # Verify error logging captured the exception type
                        mock_error.assert_called_once()
                        assert mock_error.call_args[1]["error"] == str(test_error)
                        assert mock_error.call_args[1]["exc_info"] is True