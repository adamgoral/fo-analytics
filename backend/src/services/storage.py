"""Storage service for handling document uploads and retrieval using MinIO/S3."""

import io
import os
from typing import BinaryIO, Optional
from uuid import uuid4

import aioboto3
from botocore.exceptions import ClientError, NoCredentialsError
from structlog import get_logger

from core.config import settings

logger = get_logger()


class StorageService:
    """Service for handling file storage operations with MinIO/S3."""
    
    def __init__(self):
        self.endpoint_url = f"http://{settings.minio_endpoint}"
        if settings.minio_use_ssl:
            self.endpoint_url = f"https://{settings.minio_endpoint}"
        
        self.bucket_name = settings.minio_bucket_name
        self.session = aioboto3.Session()
    
    async def create_bucket_if_not_exists(self) -> None:
        """Create the storage bucket if it doesn't exist."""
        async with self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            region_name=settings.minio_region,
            use_ssl=settings.minio_use_ssl
        ) as s3:
            try:
                await s3.head_bucket(Bucket=self.bucket_name)
                logger.info("Bucket exists", bucket=self.bucket_name)
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    await s3.create_bucket(Bucket=self.bucket_name)
                    logger.info("Created bucket", bucket=self.bucket_name)
                else:
                    logger.error("Error checking bucket", error=str(e))
                    raise
    
    async def upload_file(
        self,
        file_content: BinaryIO,
        file_name: str,
        content_type: str,
        user_id: str,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload a file to MinIO/S3.
        
        Args:
            file_content: File content as binary IO
            file_name: Original file name
            content_type: MIME type of the file
            user_id: ID of the user uploading the file
            metadata: Optional metadata to store with the file
            
        Returns:
            The S3 key of the uploaded file
        """
        # Generate unique key for the file
        file_extension = os.path.splitext(file_name)[1]
        file_key = f"{user_id}/{uuid4()}{file_extension}"
        
        # Prepare metadata
        s3_metadata = {
            'user_id': user_id,
            'original_filename': file_name,
            'content_type': content_type
        }
        if metadata:
            s3_metadata.update(metadata)
        
        async with self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            region_name=settings.minio_region,
            use_ssl=settings.minio_use_ssl
        ) as s3:
            try:
                # Upload the file
                await s3.upload_fileobj(
                    file_content,
                    self.bucket_name,
                    file_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'Metadata': s3_metadata
                    }
                )
                
                logger.info(
                    "File uploaded successfully",
                    user_id=user_id,
                    file_key=file_key,
                    original_filename=file_name
                )
                
                return file_key
                
            except Exception as e:
                logger.error(
                    "Failed to upload file",
                    user_id=user_id,
                    file_name=file_name,
                    error=str(e)
                )
                raise
    
    async def download_file(self, file_key: str) -> tuple[bytes, dict]:
        """
        Download a file from MinIO/S3.
        
        Args:
            file_key: The S3 key of the file
            
        Returns:
            Tuple of (file content, metadata)
        """
        async with self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            region_name=settings.minio_region,
            use_ssl=settings.minio_use_ssl
        ) as s3:
            try:
                # Get the object
                response = await s3.get_object(
                    Bucket=self.bucket_name,
                    Key=file_key
                )
                
                # Read the content
                content = await response['Body'].read()
                
                # Get metadata
                metadata = response.get('Metadata', {})
                metadata['ContentType'] = response.get('ContentType', 'application/octet-stream')
                metadata['ContentLength'] = response.get('ContentLength', 0)
                
                logger.info("File downloaded successfully", file_key=file_key)
                
                return content, metadata
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    logger.error("File not found", file_key=file_key)
                    raise FileNotFoundError(f"File {file_key} not found")
                else:
                    logger.error("Failed to download file", file_key=file_key, error=str(e))
                    raise
    
    async def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from MinIO/S3.
        
        Args:
            file_key: The S3 key of the file
            
        Returns:
            True if successful, False otherwise
        """
        async with self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            region_name=settings.minio_region,
            use_ssl=settings.minio_use_ssl
        ) as s3:
            try:
                await s3.delete_object(
                    Bucket=self.bucket_name,
                    Key=file_key
                )
                
                logger.info("File deleted successfully", file_key=file_key)
                return True
                
            except Exception as e:
                logger.error("Failed to delete file", file_key=file_key, error=str(e))
                return False
    
    async def generate_presigned_url(
        self,
        file_key: str,
        expiration: int = 3600
    ) -> str:
        """
        Generate a presigned URL for downloading a file.
        
        Args:
            file_key: The S3 key of the file
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL
        """
        async with self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            region_name=settings.minio_region,
            use_ssl=settings.minio_use_ssl
        ) as s3:
            try:
                url = await s3.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': file_key
                    },
                    ExpiresIn=expiration
                )
                
                logger.info(
                    "Presigned URL generated",
                    file_key=file_key,
                    expiration=expiration
                )
                
                return url
                
            except Exception as e:
                logger.error(
                    "Failed to generate presigned URL",
                    file_key=file_key,
                    error=str(e)
                )
                raise
    
    async def list_user_files(self, user_id: str) -> list[dict]:
        """
        List all files for a specific user.
        
        Args:
            user_id: The user ID
            
        Returns:
            List of file metadata
        """
        prefix = f"{user_id}/"
        files = []
        
        async with self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            region_name=settings.minio_region,
            use_ssl=settings.minio_use_ssl
        ) as s3:
            try:
                paginator = s3.get_paginator('list_objects_v2')
                
                async for page in paginator.paginate(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                ):
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            files.append({
                                'key': obj['Key'],
                                'size': obj['Size'],
                                'last_modified': obj['LastModified'].isoformat(),
                                'etag': obj.get('ETag', '').strip('"')
                            })
                
                logger.info(
                    "Listed user files",
                    user_id=user_id,
                    file_count=len(files)
                )
                
                return files
                
            except Exception as e:
                logger.error(
                    "Failed to list user files",
                    user_id=user_id,
                    error=str(e)
                )
                raise


# Create a global instance
storage_service = StorageService()