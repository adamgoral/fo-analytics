"""Tests for document API endpoints with message queue integration."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.document import Document, DocumentStatus, DocumentType
from messaging.schemas import DocumentProcessingMessage


@pytest.mark.asyncio
class TestDocumentUploadWithQueue:
    """Test document upload with RabbitMQ integration."""
    
    @pytest.fixture
    async def authenticated_client(self, async_client: AsyncClient, async_session: AsyncSession):
        """Create an authenticated client with a test user."""
        # Register a test user
        user_data = {
            "username": "queuetest",
            "email": "queuetest@example.com",
            "password": "testPassword123!",
            "full_name": "Queue Test User"
        }
        
        await async_client.post("/api/v1/auth/register", json=user_data)
        
        # Login to get access token
        login_response = await async_client.post("/api/v1/auth/login", data={
            "username": user_data["username"],
            "password": user_data["password"]
        })
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        
        # Get the user from database
        from repositories.user import UserRepository
        user_repo = UserRepository(async_session)
        user = await user_repo.get_by_email(user_data["email"])
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        yield async_client, user, headers
    
    @patch("messaging.publisher.MessagePublisher")
    @patch("services.storage.storage_service")
    async def test_upload_document_publishes_to_queue(
        self,
        mock_storage_service,
        mock_publisher_class,
        authenticated_client
    ):
        """Test that document upload publishes message to queue."""
        client, user, headers = authenticated_client
        
        # Mock storage service
        mock_storage_service.create_bucket_if_not_exists = AsyncMock()
        mock_storage_service.upload_file = AsyncMock(return_value="user123/doc456.pdf")
        
        # Mock message publisher
        mock_publisher = AsyncMock()
        mock_publisher.publish_document_processing = AsyncMock(return_value=uuid4())
        mock_publisher_class.return_value = mock_publisher
        
        # Create test file
        file_content = b"Test document for queue processing"
        file_data = {
            "file": ("strategy_doc.pdf", file_content, "application/pdf")
        }
        
        response = await client.post(
            "/api/v1/documents/upload",
            files=file_data,
            params={"document_type": "strategy_document"},
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify document was created
        assert data["original_filename"] == "strategy_doc.pdf"
        assert data["status"] == "pending"
        
        # Verify message was published
        mock_publisher.publish_document_processing.assert_called_once()
        call_args = mock_publisher.publish_document_processing.call_args[1]
        
        assert call_args["user_id"] == user.id
        assert call_args["file_key"] == "user123/doc456.pdf"
        assert call_args["filename"] == "strategy_doc.pdf"
        assert call_args["file_size"] == len(file_content)
        assert call_args["content_type"] == "application/pdf"
        assert call_args["processing_type"] == "full"
    
    @patch("messaging.publisher.MessagePublisher")
    @patch("services.storage.storage_service")
    async def test_upload_continues_on_queue_failure(
        self,
        mock_storage_service,
        mock_publisher_class,
        authenticated_client
    ):
        """Test that upload succeeds even if queue publishing fails."""
        client, user, headers = authenticated_client
        
        # Mock storage service
        mock_storage_service.create_bucket_if_not_exists = AsyncMock()
        mock_storage_service.upload_file = AsyncMock(return_value="user123/doc789.pdf")
        
        # Mock publisher to fail
        mock_publisher = AsyncMock()
        mock_publisher.publish_document_processing = AsyncMock(
            side_effect=Exception("RabbitMQ connection failed")
        )
        mock_publisher_class.return_value = mock_publisher
        
        file_data = {
            "file": ("report.pdf", b"Content", "application/pdf")
        }
        
        # Upload should still succeed
        response = await client.post(
            "/api/v1/documents/upload",
            files=file_data,
            params={"document_type": "research_report"},
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        
        # Verify publish was attempted
        mock_publisher.publish_document_processing.assert_called_once()
    
    @patch("messaging.publisher.MessagePublisher")
    async def test_process_endpoint_publishes_to_queue(
        self,
        mock_publisher_class,
        authenticated_client,
        async_session: AsyncSession
    ):
        """Test that process endpoint publishes message to queue."""
        client, user, headers = authenticated_client
        
        # Create a document
        doc = Document(
            filename="process_test.pdf",
            original_filename="process_test.pdf",
            document_type=DocumentType.STRATEGY_DOCUMENT,
            storage_path="user123/process_test.pdf",
            file_size=5000,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
            uploaded_by_id=user.id
        )
        async_session.add(doc)
        await async_session.commit()
        await async_session.refresh(doc)
        
        # Mock publisher
        mock_publisher = AsyncMock()
        mock_publisher.publish_document_processing = AsyncMock(return_value=uuid4())
        mock_publisher_class.return_value = mock_publisher
        
        # Trigger processing
        response = await client.post(
            f"/api/v1/documents/{doc.id}/process",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        
        # Verify message was published
        mock_publisher.publish_document_processing.assert_called_once()
        call_args = mock_publisher.publish_document_processing.call_args[1]
        
        assert call_args["document_id"] == doc.id
        assert call_args["user_id"] == user.id
        assert call_args["file_key"] == doc.storage_path
        assert call_args["processing_type"] == "full"
    
    @patch("messaging.publisher.MessagePublisher")
    async def test_process_force_reprocess_publishes_to_queue(
        self,
        mock_publisher_class,
        authenticated_client,
        async_session: AsyncSession
    ):
        """Test force reprocessing publishes to queue."""
        client, user, headers = authenticated_client
        
        # Create a completed document
        doc = Document(
            filename="completed.pdf",
            original_filename="completed.pdf",
            document_type=DocumentType.STRATEGY_DOCUMENT,
            storage_path="user123/completed.pdf",
            file_size=3000,
            mime_type="application/pdf",
            status=DocumentStatus.COMPLETED,
            uploaded_by_id=user.id,
            extracted_text="Previous extraction"
        )
        async_session.add(doc)
        await async_session.commit()
        await async_session.refresh(doc)
        
        # Mock publisher
        mock_publisher = AsyncMock()
        mock_publisher.publish_document_processing = AsyncMock(return_value=uuid4())
        mock_publisher_class.return_value = mock_publisher
        
        # Force reprocess
        response = await client.post(
            f"/api/v1/documents/{doc.id}/process",
            json={"force_reprocess": True},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        
        # Verify message was published
        mock_publisher.publish_document_processing.assert_called_once()
    
    @patch("messaging.publisher.MessagePublisher")
    async def test_process_already_processing_returns_error(
        self,
        mock_publisher_class,
        authenticated_client,
        async_session: AsyncSession
    ):
        """Test that processing an already processing document returns error."""
        client, user, headers = authenticated_client
        
        # Create a processing document
        doc = Document(
            filename="processing.pdf",
            original_filename="processing.pdf",
            document_type=DocumentType.STRATEGY_DOCUMENT,
            storage_path="user123/processing.pdf",
            file_size=2000,
            mime_type="application/pdf",
            status=DocumentStatus.PROCESSING,
            uploaded_by_id=user.id
        )
        async_session.add(doc)
        await async_session.commit()
        await async_session.refresh(doc)
        
        # Try to process again
        response = await client.post(
            f"/api/v1/documents/{doc.id}/process",
            headers=headers
        )
        
        assert response.status_code == 400
        assert "already being processed" in response.json()["detail"]
    
    @patch("messaging.publisher.MessagePublisher")
    async def test_process_failed_on_queue_error(
        self,
        mock_publisher_class,
        authenticated_client,
        async_session: AsyncSession
    ):
        """Test document status on queue publishing failure."""
        client, user, headers = authenticated_client
        
        # Create a document
        doc = Document(
            filename="queue_fail.pdf",
            original_filename="queue_fail.pdf",
            document_type=DocumentType.STRATEGY_DOCUMENT,
            storage_path="user123/queue_fail.pdf",
            file_size=1500,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
            uploaded_by_id=user.id
        )
        async_session.add(doc)
        await async_session.commit()
        await async_session.refresh(doc)
        
        # Mock publisher to fail
        mock_publisher = AsyncMock()
        mock_publisher.publish_document_processing = AsyncMock(
            side_effect=Exception("Queue unavailable")
        )
        mock_publisher_class.return_value = mock_publisher
        
        # Try to process
        response = await client.post(
            f"/api/v1/documents/{doc.id}/process",
            headers=headers
        )
        
        assert response.status_code == 500
        assert "Failed to queue document" in response.json()["detail"]
        
        # Verify document status was updated to failed
        await async_session.refresh(doc)
        assert doc.status == DocumentStatus.FAILED
        assert "Failed to queue" in doc.processing_error