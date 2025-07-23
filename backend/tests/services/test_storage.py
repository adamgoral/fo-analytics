"""Tests for the storage service."""

import pytest
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

from services.storage import StorageService
from botocore.exceptions import ClientError


@pytest.fixture
def storage_service():
    """Create a storage service instance."""
    return StorageService()


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client."""
    client = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_create_bucket_if_not_exists_bucket_exists(storage_service, mock_s3_client):
    """Test create_bucket_if_not_exists when bucket already exists."""
    # Mock head_bucket to succeed (bucket exists)
    mock_s3_client.head_bucket = AsyncMock()
    
    with patch.object(storage_service.session, 'client') as mock_client_context:
        mock_client_context.return_value.__aenter__.return_value = mock_s3_client
        
        await storage_service.create_bucket_if_not_exists()
        
        mock_s3_client.head_bucket.assert_called_once_with(Bucket=storage_service.bucket_name)
        mock_s3_client.create_bucket.assert_not_called()


@pytest.mark.asyncio
async def test_create_bucket_if_not_exists_bucket_missing(storage_service, mock_s3_client):
    """Test create_bucket_if_not_exists when bucket doesn't exist."""
    # Mock head_bucket to raise 404 error
    error_response = {'Error': {'Code': '404'}}
    mock_s3_client.head_bucket = AsyncMock(side_effect=ClientError(error_response, 'HeadBucket'))
    mock_s3_client.create_bucket = AsyncMock()
    
    with patch.object(storage_service.session, 'client') as mock_client_context:
        mock_client_context.return_value.__aenter__.return_value = mock_s3_client
        
        await storage_service.create_bucket_if_not_exists()
        
        mock_s3_client.head_bucket.assert_called_once_with(Bucket=storage_service.bucket_name)
        mock_s3_client.create_bucket.assert_called_once_with(Bucket=storage_service.bucket_name)


@pytest.mark.asyncio
async def test_upload_file_success(storage_service, mock_s3_client):
    """Test successful file upload."""
    # Prepare test data
    file_content = BytesIO(b"Test file content")
    file_name = "test_document.pdf"
    content_type = "application/pdf"
    user_id = "user123"
    metadata = {"category": "research"}
    
    mock_s3_client.upload_fileobj = AsyncMock()
    
    with patch.object(storage_service.session, 'client') as mock_client_context:
        mock_client_context.return_value.__aenter__.return_value = mock_s3_client
        
        file_key = await storage_service.upload_file(
            file_content=file_content,
            file_name=file_name,
            content_type=content_type,
            user_id=user_id,
            metadata=metadata
        )
        
        assert file_key.startswith(f"{user_id}/")
        assert file_key.endswith(".pdf")
        
        # Verify upload was called with correct parameters
        mock_s3_client.upload_fileobj.assert_called_once()
        call_args = mock_s3_client.upload_fileobj.call_args
        assert call_args[0][0] == file_content
        assert call_args[0][1] == storage_service.bucket_name
        assert call_args[0][2] == file_key


@pytest.mark.asyncio
async def test_download_file_success(storage_service, mock_s3_client):
    """Test successful file download."""
    file_key = "user123/test-file.pdf"
    file_content = b"Test file content"
    
    # Mock response
    mock_response = {
        'Body': AsyncMock(read=AsyncMock(return_value=file_content)),
        'ContentType': 'application/pdf',
        'ContentLength': len(file_content),
        'Metadata': {'user_id': 'user123'}
    }
    mock_s3_client.get_object = AsyncMock(return_value=mock_response)
    
    with patch.object(storage_service.session, 'client') as mock_client_context:
        mock_client_context.return_value.__aenter__.return_value = mock_s3_client
        
        content, metadata = await storage_service.download_file(file_key)
        
        assert content == file_content
        assert metadata['ContentType'] == 'application/pdf'
        assert metadata['ContentLength'] == len(file_content)
        assert metadata['user_id'] == 'user123'


@pytest.mark.asyncio
async def test_download_file_not_found(storage_service, mock_s3_client):
    """Test download file when file doesn't exist."""
    file_key = "user123/non-existent.pdf"
    
    # Mock NoSuchKey error
    error_response = {'Error': {'Code': 'NoSuchKey'}}
    mock_s3_client.get_object = AsyncMock(side_effect=ClientError(error_response, 'GetObject'))
    
    with patch.object(storage_service.session, 'client') as mock_client_context:
        mock_client_context.return_value.__aenter__.return_value = mock_s3_client
        
        with pytest.raises(FileNotFoundError):
            await storage_service.download_file(file_key)


@pytest.mark.asyncio
async def test_delete_file_success(storage_service, mock_s3_client):
    """Test successful file deletion."""
    file_key = "user123/test-file.pdf"
    
    mock_s3_client.delete_object = AsyncMock()
    
    with patch.object(storage_service.session, 'client') as mock_client_context:
        mock_client_context.return_value.__aenter__.return_value = mock_s3_client
        
        result = await storage_service.delete_file(file_key)
        
        assert result is True
        mock_s3_client.delete_object.assert_called_once_with(
            Bucket=storage_service.bucket_name,
            Key=file_key
        )


@pytest.mark.asyncio
async def test_generate_presigned_url(storage_service, mock_s3_client):
    """Test generating presigned URL."""
    file_key = "user123/test-file.pdf"
    expected_url = "https://example.com/presigned-url"
    
    mock_s3_client.generate_presigned_url = AsyncMock(return_value=expected_url)
    
    with patch.object(storage_service.session, 'client') as mock_client_context:
        mock_client_context.return_value.__aenter__.return_value = mock_s3_client
        
        url = await storage_service.generate_presigned_url(file_key)
        
        assert url == expected_url
        mock_s3_client.generate_presigned_url.assert_called_once()


@pytest.mark.asyncio
async def test_list_user_files(storage_service, mock_s3_client):
    """Test listing user files."""
    user_id = "user123"
    
    # Mock paginator response
    mock_page = {
        'Contents': [
            {
                'Key': f'{user_id}/file1.pdf',
                'Size': 1024,
                'LastModified': MagicMock(isoformat=lambda: '2023-01-01T00:00:00'),
                'ETag': '"abc123"'
            },
            {
                'Key': f'{user_id}/file2.pdf',
                'Size': 2048,
                'LastModified': MagicMock(isoformat=lambda: '2023-01-02T00:00:00'),
                'ETag': '"def456"'
            }
        ]
    }
    
    mock_paginator = AsyncMock()
    mock_paginator.paginate = MagicMock(return_value=AsyncMock(__aiter__=lambda self: self, __anext__=AsyncMock(side_effect=[mock_page, StopAsyncIteration])))
    mock_s3_client.get_paginator = MagicMock(return_value=mock_paginator)
    
    with patch.object(storage_service.session, 'client') as mock_client_context:
        mock_client_context.return_value.__aenter__.return_value = mock_s3_client
        
        files = await storage_service.list_user_files(user_id)
        
        assert len(files) == 2
        assert files[0]['key'] == f'{user_id}/file1.pdf'
        assert files[0]['size'] == 1024
        assert files[1]['key'] == f'{user_id}/file2.pdf'
        assert files[1]['size'] == 2048