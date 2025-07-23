"""Document API endpoints."""

import os
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_active_user
from core.database import get_db
from core.dependencies import get_document_repository
from core.config import settings
from models.user import User
from models.document import DocumentStatus, DocumentType
from repositories.document import DocumentRepository
from schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    DocumentProcessRequest
)
from services.storage import storage_service
from services.document_parser import DocumentParserService
from messaging.publisher import MessagePublisher
from api.websockets import notifier

router = APIRouter(prefix="/documents", tags=["documents"])

# Use settings for allowed extensions and max file size
ALLOWED_EXTENSIONS = {ext: None for ext in settings.allowed_file_extensions}
MAX_FILE_SIZE = settings.max_upload_size


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Query(...),
    current_user: User = Depends(get_current_active_user),
    document_repo: DocumentRepository = Depends(get_document_repository),
):
    """
    Upload a new document for strategy extraction.
    
    - **file**: The document file to upload (PDF, TXT, DOC, DOCX)
    - **document_type**: Type of document being uploaded
    
    Maximum file size configurable via MAX_UPLOAD_SIZE environment variable.
    """
    # Validate file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_extension} not allowed. Allowed types: {', '.join(settings.allowed_file_extensions)}"
        )
    
    # Read file content to check size
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum allowed size ({MAX_FILE_SIZE / (1024*1024):.1f}MB)"
        )
    
    # Ensure MinIO bucket exists
    await storage_service.create_bucket_if_not_exists()
    
    # Upload file to MinIO
    try:
        # Create a BytesIO object from the content
        file_content = BytesIO(content)
        
        # Upload to MinIO
        storage_key = await storage_service.upload_file(
            file_content=file_content,
            file_name=file.filename,
            content_type=file.content_type or "application/octet-stream",
            user_id=str(current_user.id),
            metadata={
                "document_type": document_type,
                "uploaded_at": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to storage: {str(e)}"
        )
    
    # Send WebSocket notification for upload started
    await notifier.document_upload_started(
        user_id=str(current_user.id),
        document_id="pending",  # Temporary ID until DB record created
        filename=file.filename
    )
    
    # Create document record
    document_data = DocumentCreate(
        filename=Path(file.filename).name,
        original_filename=file.filename,
        document_type=document_type,
        storage_path=storage_key,  # Store MinIO key instead of local path
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream"
    )
    
    document_dict = document_data.model_dump()
    document_dict["uploaded_by_id"] = current_user.id
    document_dict["status"] = DocumentStatus.PENDING
    
    try:
        document = await document_repo.create(**document_dict)
    except Exception as e:
        # If database creation fails, try to clean up the uploaded file
        await storage_service.delete_file(storage_key)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document record: {str(e)}"
        )
    
    # Publish message to processing queue
    try:
        publisher = MessagePublisher()
        await publisher.publish_document_processing(
            document_id=document.id,
            user_id=current_user.id,
            file_key=storage_key,
            filename=file.filename,
            file_size=file_size,
            content_type=file.content_type or "application/octet-stream",
            processing_type="full"
        )
    except Exception as e:
        # Log error but don't fail the upload
        # TODO: Add proper logging
        print(f"Failed to publish processing message: {str(e)}")
    
    # Send WebSocket notification for upload completed
    await notifier.document_upload_completed(
        user_id=str(current_user.id),
        document_id=str(document.id),
        filename=file.filename
    )
    
    return document


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[DocumentStatus] = None,
    document_type: Optional[DocumentType] = None,
    current_user: User = Depends(get_current_active_user),
    document_repo: DocumentRepository = Depends(get_document_repository),
):
    """
    List documents uploaded by the current user.
    
    - **skip**: Number of documents to skip (for pagination)
    - **limit**: Maximum number of documents to return
    - **status**: Filter by document status
    - **document_type**: Filter by document type
    """
    # Get documents for current user
    documents = await document_repo.get_by_user(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    # Apply filters if provided
    if status:
        documents = [d for d in documents if d.status == status]
    if document_type:
        documents = [d for d in documents if d.document_type == document_type]
    
    return DocumentListResponse(
        documents=documents,
        total=len(documents),
        skip=skip,
        limit=limit
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    document_repo: DocumentRepository = Depends(get_document_repository),
):
    """
    Get a specific document by ID.
    
    Requires authentication and ownership.
    """
    document = await document_repo.get(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check ownership
    if document.uploaded_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this document"
        )
    
    return document


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    document_repo: DocumentRepository = Depends(get_document_repository),
):
    """
    Download a document file.
    
    Requires authentication and ownership.
    """
    document = await document_repo.get(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check ownership
    if document.uploaded_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to download this document"
        )
    
    try:
        # Download file from MinIO
        file_content, metadata = await storage_service.download_file(document.storage_path)
        
        # Return file as streaming response
        return StreamingResponse(
            BytesIO(file_content),
            media_type=metadata.get('ContentType', document.mime_type),
            headers={
                "Content-Disposition": f'attachment; filename="{document.original_filename}"',
                "Content-Length": str(metadata.get('ContentLength', len(file_content)))
            }
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in storage"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    current_user: User = Depends(get_current_active_user),
    document_repo: DocumentRepository = Depends(get_document_repository),
):
    """
    Update document metadata.
    
    Requires authentication and ownership.
    """
    # Check if document exists and user owns it
    document = await document_repo.get(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.uploaded_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this document"
        )
    
    # Update document
    update_data = document_update.model_dump(exclude_unset=True)
    updated_document = await document_repo.update(document_id, **update_data)
    
    return updated_document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    document_repo: DocumentRepository = Depends(get_document_repository),
):
    """
    Delete a document and its associated file.
    
    Requires authentication and ownership.
    """
    # Check if document exists and user owns it
    document = await document_repo.get(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.uploaded_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this document"
        )
    
    # Delete file from MinIO
    try:
        await storage_service.delete_file(document.storage_path)
    except Exception as e:
        # Log error but don't fail the deletion
        # In production, this should use proper logging
        print(f"Failed to delete file {document.storage_path} from MinIO: {str(e)}")
    
    # Delete document record
    await document_repo.delete(document_id)


@router.post("/{document_id}/process", response_model=DocumentResponse)
async def process_document(
    document_id: int,
    process_request: DocumentProcessRequest = DocumentProcessRequest(),
    current_user: User = Depends(get_current_active_user),
    document_repo: DocumentRepository = Depends(get_document_repository),
):
    """
    Trigger processing of a document to extract strategies.
    
    - **force_reprocess**: Force reprocessing even if already processed
    
    Requires authentication and ownership.
    """
    # Check ownership and status
    document = await document_repo.get(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.uploaded_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to process this document"
        )
    
    # Check if already processing or completed
    if not process_request.force_reprocess:
        if document.status == DocumentStatus.PROCESSING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document is already being processed"
            )
        
        if document.status == DocumentStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document has already been processed. Set force_reprocess=true to reprocess."
            )
    
    # Update status to pending for queue processing
    updated_document = await document_repo.update(
        document_id,
        status=DocumentStatus.PENDING,
        processing_started_at=None,
        processing_completed_at=None,
        processing_error=None
    )
    
    # Publish message to processing queue
    try:
        publisher = MessagePublisher()
        await publisher.publish_document_processing(
            document_id=document.id,
            user_id=current_user.id,
            file_key=document.storage_path,
            filename=document.filename,
            file_size=document.file_size,
            content_type=document.mime_type,
            processing_type="full"
        )
        
        # Update status to indicate queued for processing
        updated_document = await document_repo.update(
            document_id,
            status=DocumentStatus.PROCESSING,
            processing_started_at=datetime.utcnow()
        )
        
    except Exception as e:
        # Update document with error
        updated_document = await document_repo.update(
            document_id,
            status=DocumentStatus.FAILED,
            processing_error=f"Failed to queue for processing: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue document for processing: {str(e)}"
        )
    
    return updated_document


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: int,
    page_number: Optional[int] = Query(None, ge=1, description="Get specific page content"),
    current_user: User = Depends(get_current_active_user),
    document_repo: DocumentRepository = Depends(get_document_repository),
):
    """
    Get the extracted text content of a document.
    
    - **page_number**: Optional page number to get specific page content (PDF only)
    
    Requires authentication and ownership.
    """
    document = await document_repo.get(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check ownership
    if document.uploaded_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this document"
        )
    
    # Check if document has been processed
    if document.status != DocumentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document has not been processed yet. Current status: {document.status}"
        )
    
    if page_number:
        # Parse document by pages
        parser_service = DocumentParserService(storage_service)
        try:
            pages = await parser_service.parse_document_by_pages(
                user_id=current_user.id,
                file_key=document.storage_path
            )
            
            if page_number > len(pages):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Page {page_number} not found. Document has {len(pages)} pages."
                )
            
            return {
                "document_id": document_id,
                "page": pages[page_number - 1],
                "total_pages": len(pages)
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve page content: {str(e)}"
            )
    else:
        # Return full document content
        return {
            "document_id": document_id,
            "content": document.extracted_text,
            "metadata": document.extracted_metadata or {}
        }


@router.get("/status/{status}", response_model=List[DocumentResponse])
async def get_documents_by_status(
    status: DocumentStatus,
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    document_repo: DocumentRepository = Depends(get_document_repository),
):
    """
    Get documents by processing status.
    
    Requires authentication. Returns only documents owned by the current user.
    """
    documents = await document_repo.get_by_status(status, user_id=current_user.id)
    
    return documents[:limit]