"""Document API endpoints."""

import os
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import get_current_active_user
from ..core.database import get_db
from ..core.dependencies import get_document_repository
from ..core.config import settings
from ..models.user import User
from ..models.document import DocumentStatus, DocumentType
from ..repositories.document import DocumentRepository
from ..schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    DocumentProcessRequest
)

router = APIRouter(prefix="/documents", tags=["documents"])

# Allowed file extensions and their MIME types
ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".md": "text/markdown",
}

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Query(...),
    current_user: User = Depends(get_current_active_user),
    document_repo: DocumentRepository = Depends(get_document_repository),
):
    """
    Upload a new document for strategy extraction.
    
    - **file**: The document file to upload (PDF, DOC, DOCX, TXT, MD)
    - **document_type**: Type of document being uploaded
    
    Maximum file size: 10MB
    """
    # Validate file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_extension} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS.keys())}"
        )
    
    # Validate MIME type
    if file.content_type not in ALLOWED_EXTENSIONS.values():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid MIME type: {file.content_type}"
        )
    
    # Read file content to check size
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)"
        )
    
    # Create storage directory if it doesn't exist
    storage_dir = Path(settings.upload_dir) / str(current_user.id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}".replace(" ", "_")
    storage_path = storage_dir / safe_filename
    
    # Save file to disk
    try:
        with open(storage_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Create document record
    document_data = DocumentCreate(
        filename=safe_filename,
        original_filename=file.filename,
        document_type=document_type,
        storage_path=str(storage_path),
        file_size=file_size,
        mime_type=file.content_type
    )
    
    document_dict = document_data.model_dump()
    document_dict["uploaded_by_id"] = current_user.id
    document_dict["status"] = DocumentStatus.PENDING
    
    document = await document_repo.create(**document_dict)
    
    # TODO: Trigger document processing (e.g., send to queue)
    
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
    
    # Delete file from disk
    try:
        if os.path.exists(document.storage_path):
            os.remove(document.storage_path)
    except Exception as e:
        # Log error but don't fail the deletion
        print(f"Failed to delete file {document.storage_path}: {str(e)}")
    
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
    
    # Update status to processing
    updated_document = await document_repo.update(
        document_id,
        status=DocumentStatus.PROCESSING,
        processing_started_at=datetime.utcnow()
    )
    
    # TODO: Trigger actual document processing (e.g., send to queue)
    
    return updated_document


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