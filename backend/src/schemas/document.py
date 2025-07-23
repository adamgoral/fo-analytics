"""Document-related schemas for API endpoints."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from models.document import DocumentType, DocumentStatus


class DocumentBase(BaseModel):
    """Base document schema."""
    
    document_type: DocumentType


class DocumentCreate(DocumentBase):
    """Schema for creating a document (used internally after file upload)."""
    
    filename: str
    original_filename: str
    storage_path: str
    file_size: int
    mime_type: str


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    
    document_type: Optional[DocumentType] = None
    status: Optional[DocumentStatus] = None
    extracted_metadata: Optional[Dict] = None


class DocumentResponse(BaseModel):
    """Document response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    filename: str
    original_filename: str
    document_type: DocumentType
    
    # Storage info
    storage_path: str
    file_size: int
    mime_type: str
    
    # Processing status
    status: DocumentStatus
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    processing_error: Optional[str]
    
    # Metadata
    extracted_metadata: Optional[Dict]
    uploaded_by_id: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    """Response for document list endpoints."""
    
    documents: List[DocumentResponse]
    total: int
    skip: int
    limit: int


class DocumentProcessRequest(BaseModel):
    """Request to process a document."""
    
    force_reprocess: bool = False