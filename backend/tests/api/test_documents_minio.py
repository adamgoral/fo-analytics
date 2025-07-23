"""Tests for document API endpoints with MinIO integration."""

import pytest
from unittest.mock import AsyncMock, patch
from io import BytesIO
from datetime import datetime
from fastapi import status
from httpx import AsyncClient

from models.document import DocumentStatus, DocumentType, Document
from models.user import User, UserRole
from repositories.document import DocumentRepository
from repositories.user import UserRepository
from core.dependencies import get_document_repository
from core.security import create_access_token


@pytest.fixture
async def test_user(async_session) -> User:
    """Create a test user."""
    user_repo = UserRepository(async_session)
    user = await user_repo.create(
        email="test@example.com",
        username="testuser",
        password_hash="$2b$12$test",
        role=UserRole.ANALYST
    )
    return user


@pytest.fixture
async def auth_headers(test_user: User) -> dict:
    """Create authentication headers with JWT token."""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_document(async_session, test_user: User) -> Document:
    """Create a test document."""
    doc_repo = DocumentRepository(async_session)
    document = await doc_repo.create(
        filename="test.pdf",
        original_filename="test_document.pdf",
        document_type=DocumentType.RESEARCH_REPORT,
        storage_path="user123/test-file.pdf",
        file_size=1024,
        mime_type="application/pdf",
        uploaded_by_id=test_user.id,
        status=DocumentStatus.PENDING
    )
    return document


@pytest.mark.asyncio
async def test_upload_document_to_minio(async_client: AsyncClient, test_user: User, auth_headers: dict):
    """Test document upload to MinIO storage."""
    # Create test file
    file_content = b"Test PDF content"
    files = {"file": ("test_document.pdf", BytesIO(file_content), "application/pdf")}
    
    with patch("api.documents.storage_service") as mock_storage:
        # Mock storage service methods
        mock_storage.create_bucket_if_not_exists = AsyncMock()
        mock_storage.upload_file = AsyncMock(return_value="user123/unique-file-key.pdf")
        
        response = await async_client.post(
            "/api/v1/documents/upload",
            files=files,
            params={"document_type": DocumentType.RESEARCH_REPORT},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        # Verify response
        assert data["original_filename"] == "test_document.pdf"
        assert data["document_type"] == DocumentType.RESEARCH_REPORT
        assert data["status"] == DocumentStatus.PENDING
        assert data["storage_path"] == "user123/unique-file-key.pdf"
        assert data["file_size"] == len(file_content)
        assert data["mime_type"] == "application/pdf"
        
        # Verify storage service was called
        mock_storage.create_bucket_if_not_exists.assert_called_once()
        mock_storage.upload_file.assert_called_once()


@pytest.mark.asyncio
async def test_upload_document_invalid_file_type(async_client: AsyncClient, test_user: User, auth_headers: dict):
    """Test document upload with invalid file type."""
    files = {"file": ("test.exe", BytesIO(b"executable"), "application/x-msdownload")}
    
    response = await async_client.post(
        "/api/v1/documents/upload",
        files=files,
        params={"document_type": DocumentType.RESEARCH_REPORT},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "not allowed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_document_file_too_large(async_client: AsyncClient, test_user: User, auth_headers: dict):
    """Test document upload with file exceeding size limit."""
    # Create a file larger than the limit
    large_content = b"x" * (101 * 1024 * 1024)  # 101MB
    files = {"file": ("large_file.pdf", BytesIO(large_content), "application/pdf")}
    
    response = await async_client.post(
        "/api/v1/documents/upload",
        files=files,
        params={"document_type": DocumentType.RESEARCH_REPORT},
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    assert "exceeds maximum" in response.json()["detail"]


@pytest.mark.asyncio
async def test_download_document_from_minio(async_client: AsyncClient, test_user: User, auth_headers: dict, test_document):
    """Test document download from MinIO storage."""
    file_content = b"Test PDF content"
    
    with patch("api.documents.storage_service") as mock_storage:
        # Mock download_file
        mock_storage.download_file = AsyncMock(return_value=(
            file_content,
            {
                'ContentType': 'application/pdf',
                'ContentLength': len(file_content)
            }
        ))
        
        response = await async_client.get(
            f"/api/v1/documents/{test_document.id}/download",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.content == file_content
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers["content-disposition"] == f'attachment; filename="{test_document.original_filename}"'
        
        # Verify storage service was called
        mock_storage.download_file.assert_called_once_with(test_document.storage_path)


@pytest.mark.asyncio
async def test_download_document_not_found_in_storage(async_client: AsyncClient, test_user: User, auth_headers: dict, test_document):
    """Test download when file not found in MinIO."""
    with patch("api.documents.storage_service") as mock_storage:
        # Mock download_file to raise FileNotFoundError
        mock_storage.download_file = AsyncMock(side_effect=FileNotFoundError("File not found"))
        
        response = await async_client.get(
            f"/api/v1/documents/{test_document.id}/download",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "File not found in storage" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_document_removes_from_minio(async_client: AsyncClient, test_user: User, auth_headers: dict, test_document):
    """Test document deletion removes file from MinIO."""
    with patch("api.documents.storage_service") as mock_storage:
        # Mock delete_file
        mock_storage.delete_file = AsyncMock(return_value=True)
        
        response = await async_client.delete(
            f"/api/v1/documents/{test_document.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify storage service was called
        mock_storage.delete_file.assert_called_once_with(test_document.storage_path)


@pytest.mark.asyncio
async def test_upload_document_storage_failure(async_client: AsyncClient, test_user: User, auth_headers: dict):
    """Test document upload when MinIO storage fails."""
    file_content = b"Test PDF content"
    files = {"file": ("test_document.pdf", BytesIO(file_content), "application/pdf")}
    
    with patch("api.documents.storage_service") as mock_storage:
        # Mock storage failure
        mock_storage.create_bucket_if_not_exists = AsyncMock()
        mock_storage.upload_file = AsyncMock(side_effect=Exception("Storage error"))
        
        response = await async_client.post(
            "/api/v1/documents/upload",
            files=files,
            params={"document_type": DocumentType.RESEARCH_REPORT},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to upload file to storage" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_document_cleanup_on_db_failure(async_client: AsyncClient, test_user: User, auth_headers: dict):
    """Test that uploaded file is cleaned up if database creation fails."""
    file_content = b"Test PDF content"
    files = {"file": ("test_document.pdf", BytesIO(file_content), "application/pdf")}
    
    with patch("api.documents.storage_service") as mock_storage:
        # Mock the document repository dependency
        mock_doc_repo = AsyncMock()
        mock_doc_repo.create = AsyncMock(side_effect=Exception("DB error"))
        
        async def override_get_document_repository():
            return mock_doc_repo
        
        async_client.app.dependency_overrides[get_document_repository] = override_get_document_repository
        
        try:
            # Mock successful upload but failed DB creation
            mock_storage.create_bucket_if_not_exists = AsyncMock()
            mock_storage.upload_file = AsyncMock(return_value="user123/file-key.pdf")
            mock_storage.delete_file = AsyncMock()
            
            response = await async_client.post(
                "/api/v1/documents/upload",
                files=files,
                params={"document_type": DocumentType.RESEARCH_REPORT},
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # Verify cleanup was attempted
            mock_storage.delete_file.assert_called_once_with("user123/file-key.pdf")
        finally:
            # Clean up dependency override
            async_client.app.dependency_overrides.clear()