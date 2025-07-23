"""Tests for document-related schemas."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from schemas.document import DocumentCreate, DocumentUpdate, DocumentResponse
from models.document import DocumentType, DocumentStatus


class TestDocumentSchemas:
    """Test document schema validation."""
    
    def test_document_create_valid(self):
        """Test creating valid DocumentCreate schema."""
        data = {
            "filename": "test_document.pdf",
            "document_type": DocumentType.STRATEGY_DOCUMENT.value
        }
        
        doc = DocumentCreate(**data)
        assert doc.filename == "test_document.pdf"
        assert doc.document_type == DocumentType.STRATEGY_DOCUMENT
    
    def test_document_create_invalid_type(self):
        """Test DocumentCreate with invalid document type."""
        data = {
            "filename": "test_document.pdf",
            "document_type": "invalid_type"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("document_type",) for error in errors)
    
    def test_document_create_missing_filename(self):
        """Test DocumentCreate with missing filename."""
        data = {
            "document_type": DocumentType.STRATEGY_DOCUMENT.value
        }
        
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("filename",) for error in errors)
    
    def test_document_update_partial(self):
        """Test DocumentUpdate with partial data."""
        data = {
            "status": DocumentStatus.COMPLETED.value
        }
        
        update = DocumentUpdate(**data)
        assert update.status == DocumentStatus.COMPLETED
        assert update.page_count is None
        assert update.processing_metadata is None
    
    def test_document_update_all_fields(self):
        """Test DocumentUpdate with all fields."""
        data = {
            "status": DocumentStatus.COMPLETED.value,
            "page_count": 10,
            "processing_metadata": {"engine": "tesseract", "version": "5.0"}
        }
        
        update = DocumentUpdate(**data)
        assert update.status == DocumentStatus.COMPLETED
        assert update.page_count == 10
        assert update.processing_metadata == {"engine": "tesseract", "version": "5.0"}
    
    def test_document_response(self):
        """Test DocumentResponse schema."""
        data = {
            "id": 1,
            "filename": "test_document.pdf",
            "original_filename": "original_test.pdf",
            "document_type": DocumentType.STRATEGY_DOCUMENT.value,
            "storage_path": "/path/to/document.pdf",
            "file_size": 1024,
            "mime_type": "application/pdf",
            "status": DocumentStatus.COMPLETED.value,
            "page_count": 10,
            "processing_metadata": {"engine": "tesseract"},
            "uploaded_by_id": 1,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00"
        }
        
        response = DocumentResponse(**data)
        assert response.id == 1
        assert response.filename == "test_document.pdf"
        assert response.original_filename == "original_test.pdf"
        assert response.document_type == DocumentType.STRATEGY_DOCUMENT
        assert response.status == DocumentStatus.COMPLETED
        assert response.page_count == 10