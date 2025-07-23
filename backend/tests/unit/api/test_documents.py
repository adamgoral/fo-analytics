"""Tests for document API endpoints."""

import pytest
import os
import tempfile
from io import BytesIO
from unittest.mock import AsyncMock, Mock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.models.user import User, UserRole
from src.models.document import Document, DocumentStatus, DocumentType


@pytest.mark.asyncio
class TestDocumentsAPI:
    """Test document management API endpoints."""
    
    @pytest.fixture
    async def authenticated_client(self, async_client: AsyncClient, async_session: AsyncSession):
        """Create an authenticated client with a test user."""
        # Register a test user
        user_data = {
            "name": "Doc Test User",
            "email": "doctest@example.com",
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
    
    async def test_upload_document_success(self, authenticated_client):
        """Test successful document upload."""
        client, user, headers = authenticated_client
        
        # Create a test file
        file_content = b"Test document content"
        file_data = {
            "file": ("test.pdf", file_content, "application/pdf")
        }
        
        # Mock settings upload directory
        with patch('src.api.documents.settings.upload_dir', '/tmp/test_uploads'):
            # Create temp directory
            os.makedirs(f'/tmp/test_uploads/{user.id}', exist_ok=True)
            
            response = await client.post(
                "/api/v1/documents/upload",
                files=file_data,
                params={"document_type": DocumentType.RESEARCH_REPORT.value},
                headers=headers
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data["original_filename"] == "test.pdf"
        assert data["document_type"] == DocumentType.RESEARCH_REPORT.value
        assert data["status"] == DocumentStatus.PENDING.value
        assert data["file_size"] == len(file_content)
        assert data["mime_type"] == "application/pdf"
        assert data["uploaded_by_id"] == user.id
        
        # Cleanup
        if os.path.exists(f'/tmp/test_uploads/{user.id}'):
            import shutil
            shutil.rmtree(f'/tmp/test_uploads/{user.id}')
    
    async def test_upload_document_invalid_extension(self, authenticated_client):
        """Test upload with invalid file extension."""
        client, user, headers = authenticated_client
        
        file_data = {
            "file": ("test.exe", b"content", "application/x-executable")
        }
        
        response = await client.post(
            "/api/v1/documents/upload",
            files=file_data,
            params={"document_type": DocumentType.RESEARCH_REPORT.value},
            headers=headers
        )
        
        assert response.status_code == 400
        assert "File type .exe not allowed" in response.json()["detail"]
    
    async def test_upload_document_invalid_mime_type(self, authenticated_client):
        """Test upload with invalid MIME type."""
        client, user, headers = authenticated_client
        
        file_data = {
            "file": ("test.pdf", b"content", "application/x-executable")
        }
        
        response = await client.post(
            "/api/v1/documents/upload",
            files=file_data,
            params={"document_type": DocumentType.RESEARCH_REPORT.value},
            headers=headers
        )
        
        assert response.status_code == 400
        assert "Invalid MIME type" in response.json()["detail"]
    
    async def test_upload_document_file_too_large(self, authenticated_client):
        """Test upload with file exceeding size limit."""
        client, user, headers = authenticated_client
        
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)
        file_data = {
            "file": ("large.pdf", large_content, "application/pdf")
        }
        
        response = await client.post(
            "/api/v1/documents/upload",
            files=file_data,
            params={"document_type": DocumentType.RESEARCH_REPORT.value},
            headers=headers
        )
        
        assert response.status_code == 413
        assert "exceeds maximum allowed size" in response.json()["detail"]
    
    async def test_upload_document_unauthenticated(self, async_client: AsyncClient):
        """Test upload without authentication."""
        file_data = {
            "file": ("test.pdf", b"content", "application/pdf")
        }
        
        response = await async_client.post(
            "/api/v1/documents/upload",
            files=file_data,
            params={"document_type": DocumentType.RESEARCH_REPORT.value}
        )
        
        assert response.status_code == 403  # HTTPBearer returns 403 for unauthenticated
    
    async def test_list_documents(self, authenticated_client, async_session: AsyncSession):
        """Test listing user's documents."""
        client, user, headers = authenticated_client
        
        # Create test documents
        docs = []
        for i in range(3):
            doc = Document(
                filename=f"file_{i}.pdf",
                original_filename=f"original_{i}.pdf",
                document_type=DocumentType.RESEARCH_REPORT,
                storage_path=f"/path/to/file_{i}.pdf",
                file_size=1000 + i,
                mime_type="application/pdf",
                status=DocumentStatus.COMPLETED,
                uploaded_by_id=user.id
            )
            async_session.add(doc)
            docs.append(doc)
        
        await async_session.commit()
        
        response = await client.get("/api/v1/documents/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["documents"]) == 3
        assert data["skip"] == 0
        assert data["limit"] == 100
    
    async def test_list_documents_with_filters(self, authenticated_client, async_session: AsyncSession):
        """Test listing documents with status and type filters."""
        client, user, headers = authenticated_client
        
        # Create documents with different statuses and types
        doc1 = Document(
            filename="pending.pdf",
            original_filename="pending.pdf",
            document_type=DocumentType.RESEARCH_REPORT,
            storage_path="/path/to/pending.pdf",
            file_size=1000,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
            uploaded_by_id=user.id
        )
        doc2 = Document(
            filename="completed.pdf",
            original_filename="completed.pdf",
            document_type=DocumentType.STRATEGY_DOCUMENT,
            storage_path="/path/to/completed.pdf",
            file_size=2000,
            mime_type="application/pdf",
            status=DocumentStatus.COMPLETED,
            uploaded_by_id=user.id
        )
        
        async_session.add(doc1)
        async_session.add(doc2)
        await async_session.commit()
        
        # Filter by status
        response = await client.get(
            "/api/v1/documents/",
            params={"status": DocumentStatus.PENDING.value},
            headers=headers
        )
        data = response.json()
        assert len(data["documents"]) == 1
        assert data["documents"][0]["status"] == DocumentStatus.PENDING.value
        
        # Filter by document type
        response = await client.get(
            "/api/v1/documents/",
            params={"document_type": DocumentType.STRATEGY_DOCUMENT.value},
            headers=headers
        )
        data = response.json()
        assert len(data["documents"]) == 1
        assert data["documents"][0]["document_type"] == DocumentType.STRATEGY_DOCUMENT.value
    
    async def test_list_documents_pagination(self, authenticated_client, async_session: AsyncSession):
        """Test document list pagination."""
        client, user, headers = authenticated_client
        
        # Create 5 documents
        for i in range(5):
            doc = Document(
                filename=f"doc_{i}.pdf",
                original_filename=f"doc_{i}.pdf",
                document_type=DocumentType.RESEARCH_REPORT,
                storage_path=f"/path/to/doc_{i}.pdf",
                file_size=1000,
                mime_type="application/pdf",
                status=DocumentStatus.COMPLETED,
                uploaded_by_id=user.id
            )
            async_session.add(doc)
        
        await async_session.commit()
        
        # Get first page
        response = await client.get("/api/v1/documents/?skip=0&limit=2", headers=headers)
        data = response.json()
        assert len(data["documents"]) == 2
        assert data["skip"] == 0
        assert data["limit"] == 2
        
        # Get second page
        response = await client.get("/api/v1/documents/?skip=2&limit=2", headers=headers)
        data = response.json()
        assert len(data["documents"]) == 2
        assert data["skip"] == 2
    
    async def test_get_document_by_id(self, authenticated_client, async_session: AsyncSession):
        """Test getting a specific document."""
        client, user, headers = authenticated_client
        
        # Create a document
        doc = Document(
            filename="test.pdf",
            original_filename="test.pdf",
            document_type=DocumentType.RESEARCH_REPORT,
            storage_path="/path/to/test.pdf",
            file_size=1000,
            mime_type="application/pdf",
            status=DocumentStatus.COMPLETED,
            uploaded_by_id=user.id
        )
        async_session.add(doc)
        await async_session.commit()
        await async_session.refresh(doc)
        
        response = await client.get(f"/api/v1/documents/{doc.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc.id
        assert data["filename"] == doc.filename
        assert data["document_type"] == doc.document_type.value
    
    async def test_get_document_not_found(self, authenticated_client):
        """Test getting non-existent document."""
        client, user, headers = authenticated_client
        
        response = await client.get("/api/v1/documents/99999", headers=headers)
        
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]
    
    async def test_get_document_not_owner(self, authenticated_client, async_session: AsyncSession):
        """Test getting document owned by another user."""
        client, user, headers = authenticated_client
        
        # Create another user
        other_user = User(
            email="other@example.com",
            username="other",
            full_name="Other User",
            hashed_password="hashed",
            role=UserRole.VIEWER,
            is_active=True,
            is_verified=True
        )
        async_session.add(other_user)
        await async_session.commit()
        await async_session.refresh(other_user)
        
        # Create document owned by other user
        doc = Document(
            filename="other.pdf",
            original_filename="other.pdf",
            document_type=DocumentType.RESEARCH_REPORT,
            storage_path="/path/to/other.pdf",
            file_size=1000,
            mime_type="application/pdf",
            status=DocumentStatus.COMPLETED,
            uploaded_by_id=other_user.id
        )
        async_session.add(doc)
        await async_session.commit()
        await async_session.refresh(doc)
        
        response = await client.get(f"/api/v1/documents/{doc.id}", headers=headers)
        
        assert response.status_code == 403
        assert "Not authorized to access this document" in response.json()["detail"]
    
    async def test_update_document(self, authenticated_client, async_session: AsyncSession):
        """Test updating document metadata."""
        client, user, headers = authenticated_client
        
        # Create a document
        doc = Document(
            filename="update.pdf",
            original_filename="update.pdf",
            document_type=DocumentType.RESEARCH_REPORT,
            storage_path="/path/to/update.pdf",
            file_size=1000,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
            uploaded_by_id=user.id
        )
        async_session.add(doc)
        await async_session.commit()
        await async_session.refresh(doc)
        
        # Update document
        update_data = {
            "document_type": DocumentType.STRATEGY_DOCUMENT.value,
            "status": DocumentStatus.COMPLETED.value,
            "extracted_metadata": {"key": "value"}
        }
        
        response = await client.patch(
            f"/api/v1/documents/{doc.id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["document_type"] == DocumentType.STRATEGY_DOCUMENT.value
        assert data["status"] == DocumentStatus.COMPLETED.value
        assert data["extracted_metadata"] == {"key": "value"}
    
    async def test_update_document_not_owner(self, authenticated_client, async_session: AsyncSession):
        """Test updating document owned by another user."""
        client, user, headers = authenticated_client
        
        # Create another user and their document
        other_user = User(
            email="other2@example.com",
            username="other2",
            full_name="Other User 2",
            hashed_password="hashed",
            role=UserRole.VIEWER,
            is_active=True,
            is_verified=True
        )
        async_session.add(other_user)
        await async_session.commit()
        
        doc = Document(
            filename="other.pdf",
            original_filename="other.pdf",
            document_type=DocumentType.RESEARCH_REPORT,
            storage_path="/path/to/other.pdf",
            file_size=1000,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
            uploaded_by_id=other_user.id
        )
        async_session.add(doc)
        await async_session.commit()
        await async_session.refresh(doc)
        
        update_data = {"status": DocumentStatus.COMPLETED.value}
        
        response = await client.patch(
            f"/api/v1/documents/{doc.id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 403
        assert "Not authorized to update this document" in response.json()["detail"]
    
    async def test_delete_document(self, authenticated_client, async_session: AsyncSession):
        """Test deleting a document."""
        client, user, headers = authenticated_client
        
        # Create a document with a mock file
        doc = Document(
            filename="delete.pdf",
            original_filename="delete.pdf",
            document_type=DocumentType.RESEARCH_REPORT,
            storage_path="/tmp/delete.pdf",
            file_size=1000,
            mime_type="application/pdf",
            status=DocumentStatus.COMPLETED,
            uploaded_by_id=user.id
        )
        async_session.add(doc)
        await async_session.commit()
        await async_session.refresh(doc)
        
        # Create mock file
        with open("/tmp/delete.pdf", "wb") as f:
            f.write(b"test content")
        
        response = await client.delete(f"/api/v1/documents/{doc.id}", headers=headers)
        
        assert response.status_code == 204
        
        # Verify file was deleted
        assert not os.path.exists("/tmp/delete.pdf")
        
        # Verify document was deleted from database
        response = await client.get(f"/api/v1/documents/{doc.id}", headers=headers)
        assert response.status_code == 404
    
    async def test_delete_document_not_owner(self, authenticated_client, async_session: AsyncSession):
        """Test deleting document owned by another user."""
        client, user, headers = authenticated_client
        
        # Create another user and their document
        other_user = User(
            email="other3@example.com",
            username="other3",
            full_name="Other User 3",
            hashed_password="hashed",
            role=UserRole.VIEWER,
            is_active=True,
            is_verified=True
        )
        async_session.add(other_user)
        await async_session.commit()
        
        doc = Document(
            filename="other.pdf",
            original_filename="other.pdf",
            document_type=DocumentType.RESEARCH_REPORT,
            storage_path="/path/to/other.pdf",
            file_size=1000,
            mime_type="application/pdf",
            status=DocumentStatus.COMPLETED,
            uploaded_by_id=other_user.id
        )
        async_session.add(doc)
        await async_session.commit()
        await async_session.refresh(doc)
        
        response = await client.delete(f"/api/v1/documents/{doc.id}", headers=headers)
        
        assert response.status_code == 403
        assert "Not authorized to delete this document" in response.json()["detail"]
    
    async def test_process_document(self, authenticated_client, async_session: AsyncSession):
        """Test triggering document processing."""
        client, user, headers = authenticated_client
        
        # Create a pending document
        doc = Document(
            filename="process.pdf",
            original_filename="process.pdf",
            document_type=DocumentType.RESEARCH_REPORT,
            storage_path="/path/to/process.pdf",
            file_size=1000,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
            uploaded_by_id=user.id
        )
        async_session.add(doc)
        await async_session.commit()
        await async_session.refresh(doc)
        
        response = await client.post(f"/api/v1/documents/{doc.id}/process", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == DocumentStatus.PROCESSING.value
        assert data["processing_started_at"] is not None
    
    async def test_process_document_already_processing(self, authenticated_client, async_session: AsyncSession):
        """Test processing a document that's already being processed."""
        client, user, headers = authenticated_client
        
        # Create a processing document
        doc = Document(
            filename="processing.pdf",
            original_filename="processing.pdf",
            document_type=DocumentType.RESEARCH_REPORT,
            storage_path="/path/to/processing.pdf",
            file_size=1000,
            mime_type="application/pdf",
            status=DocumentStatus.PROCESSING,
            uploaded_by_id=user.id,
            processing_started_at=datetime.utcnow()
        )
        async_session.add(doc)
        await async_session.commit()
        await async_session.refresh(doc)
        
        response = await client.post(f"/api/v1/documents/{doc.id}/process", headers=headers)
        
        assert response.status_code == 400
        assert "already being processed" in response.json()["detail"]
    
    async def test_process_document_force_reprocess(self, authenticated_client, async_session: AsyncSession):
        """Test force reprocessing a completed document."""
        client, user, headers = authenticated_client
        
        # Create a completed document
        doc = Document(
            filename="completed.pdf",
            original_filename="completed.pdf",
            document_type=DocumentType.RESEARCH_REPORT,
            storage_path="/path/to/completed.pdf",
            file_size=1000,
            mime_type="application/pdf",
            status=DocumentStatus.COMPLETED,
            uploaded_by_id=user.id,
            processing_completed_at=datetime.utcnow()
        )
        async_session.add(doc)
        await async_session.commit()
        await async_session.refresh(doc)
        
        # Try without force - should fail
        response = await client.post(f"/api/v1/documents/{doc.id}/process", headers=headers)
        assert response.status_code == 400
        assert "already been processed" in response.json()["detail"]
        
        # Try with force - should succeed
        response = await client.post(
            f"/api/v1/documents/{doc.id}/process",
            json={"force_reprocess": True},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == DocumentStatus.PROCESSING.value
    
    async def test_get_documents_by_status(self, authenticated_client, async_session: AsyncSession):
        """Test getting documents by status."""
        client, user, headers = authenticated_client
        
        # Create documents with different statuses
        statuses = [
            DocumentStatus.PENDING,
            DocumentStatus.PROCESSING,
            DocumentStatus.COMPLETED,
            DocumentStatus.FAILED
        ]
        
        for i, status in enumerate(statuses):
            doc = Document(
                filename=f"{status.value}.pdf",
                original_filename=f"{status.value}.pdf",
                document_type=DocumentType.RESEARCH_REPORT,
                storage_path=f"/path/to/{status.value}.pdf",
                file_size=1000,
                mime_type="application/pdf",
                status=status,
                uploaded_by_id=user.id
            )
            async_session.add(doc)
        
        await async_session.commit()
        
        # Get completed documents
        response = await client.get(f"/api/v1/documents/status/{DocumentStatus.COMPLETED.value}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert all(doc["status"] == DocumentStatus.COMPLETED.value for doc in data)
    
    async def test_get_documents_by_status_with_limit(self, authenticated_client, async_session: AsyncSession):
        """Test getting documents by status with limit."""
        client, user, headers = authenticated_client
        
        # Create multiple pending documents
        for i in range(5):
            doc = Document(
                filename=f"pending_{i}.pdf",
                original_filename=f"pending_{i}.pdf",
                document_type=DocumentType.RESEARCH_REPORT,
                storage_path=f"/path/to/pending_{i}.pdf",
                file_size=1000,
                mime_type="application/pdf",
                status=DocumentStatus.PENDING,
                uploaded_by_id=user.id
            )
            async_session.add(doc)
        
        await async_session.commit()
        
        # Get with limit
        response = await client.get(
            f"/api/v1/documents/status/{DocumentStatus.PENDING.value}?limit=2",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2