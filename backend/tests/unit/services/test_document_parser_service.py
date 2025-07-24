"""Tests for document parser service."""

import pytest
import tempfile
import os
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from io import BytesIO

from src.services.document_parser import DocumentParserService, DocumentParseError


@pytest.mark.asyncio
class TestDocumentParserService:
    """Test document parser service functionality."""
    
    @pytest.fixture
    def parser_service(self):
        """Create a document parser service instance."""
        return DocumentParserService()
    
    @pytest.fixture
    def mock_pdf_content(self):
        """Create mock PDF content."""
        return b"%PDF-1.4\n%Mock PDF content\n%%EOF"
    
    async def test_parse_pdf_success(self, parser_service, mock_pdf_content):
        """Test successful PDF parsing."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(mock_pdf_content)
            tmp_path = tmp.name
        
        try:
            # Mock PyMuPDFReader
            with patch('src.services.document_parser.PyMuPDFReader') as mock_reader_class:
                mock_reader = Mock()
                mock_doc = Mock()
                mock_doc.text = "This is a test investment strategy document."
                mock_doc.metadata = {"page": 1, "total_pages": 5}
                mock_reader.load_data.return_value = [mock_doc]
                mock_reader_class.return_value = mock_reader
                
                # Parse the document
                result = await parser_service.parse_document(tmp_path)
                
                assert result["success"] is True
                assert result["content_type"] == "application/pdf"
                assert result["extracted_text"] == "This is a test investment strategy document."
                assert result["metadata"]["pages"] == 5
                assert result["metadata"]["file_size"] > 0
                
        finally:
            os.unlink(tmp_path)
    
    async def test_parse_text_file_success(self, parser_service):
        """Test successful text file parsing."""
        content = "Simple text strategy: Buy low, sell high."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            result = await parser_service.parse_document(tmp_path)
            
            assert result["success"] is True
            assert result["content_type"] == "text/plain"
            assert result["extracted_text"] == content
            assert result["metadata"]["pages"] == 1
            
        finally:
            os.unlink(tmp_path)
    
    async def test_parse_unsupported_file_type(self, parser_service):
        """Test parsing unsupported file type."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as tmp:
            tmp.write(b"unsupported content")
            tmp_path = tmp.name
        
        try:
            with pytest.raises(DocumentParseError) as exc_info:
                await parser_service.parse_document(tmp_path)
            
            assert "Unsupported file type" in str(exc_info.value)
            
        finally:
            os.unlink(tmp_path)
    
    async def test_parse_nonexistent_file(self, parser_service):
        """Test parsing nonexistent file."""
        with pytest.raises(DocumentParseError) as exc_info:
            await parser_service.parse_document("/nonexistent/file.pdf")
        
        assert "File not found" in str(exc_info.value)
    
    async def test_parse_corrupted_pdf(self, parser_service):
        """Test parsing corrupted PDF file."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"Not a real PDF content")
            tmp_path = tmp.name
        
        try:
            # Mock PyMuPDFReader to raise exception
            with patch('src.services.document_parser.PyMuPDFReader') as mock_reader_class:
                mock_reader_class.side_effect = Exception("Invalid PDF structure")
                
                with pytest.raises(DocumentParseError) as exc_info:
                    await parser_service.parse_document(tmp_path)
                
                assert "Failed to parse PDF" in str(exc_info.value)
                
        finally:
            os.unlink(tmp_path)
    
    async def test_get_basic_info_pdf(self, parser_service, mock_pdf_content):
        """Test getting basic info from PDF."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(mock_pdf_content)
            tmp_path = tmp.name
        
        try:
            # Mock PyMuPDFReader for basic info
            with patch('src.services.document_parser.PyMuPDFReader') as mock_reader_class:
                mock_reader = Mock()
                mock_doc1 = Mock(metadata={"page": 1, "total_pages": 10})
                mock_doc2 = Mock(metadata={"page": 2, "total_pages": 10})
                mock_reader.load_data.return_value = [mock_doc1, mock_doc2]
                mock_reader_class.return_value = mock_reader
                
                info = await parser_service.get_basic_info(tmp_path)
                
                assert info["pages"] == 10
                assert info["file_size"] == len(mock_pdf_content)
                assert info["content_type"] == "application/pdf"
                
        finally:
            os.unlink(tmp_path)
    
    async def test_extract_text_chunks(self, parser_service):
        """Test extracting text in chunks."""
        long_text = " ".join([f"Sentence {i}." for i in range(1000)])
        
        chunks = await parser_service.extract_text_chunks(long_text, chunk_size=100)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 120 for chunk in chunks)  # Allow some overlap
        assert "Sentence 0." in chunks[0]
        assert "Sentence 999." in chunks[-1]
    
    async def test_parse_document_with_metadata_extraction(self, parser_service):
        """Test parsing document with metadata extraction."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"%PDF-1.4\n%Test PDF\n%%EOF")
            tmp_path = tmp.name
        
        try:
            with patch('src.services.document_parser.PyMuPDFReader') as mock_reader_class:
                mock_reader = Mock()
                mock_doc = Mock()
                mock_doc.text = "Investment strategy document with metadata."
                mock_doc.metadata = {
                    "page": 1,
                    "total_pages": 3,
                    "author": "Test Author",
                    "title": "Test Strategy",
                    "creation_date": "2023-01-01"
                }
                mock_reader.load_data.return_value = [mock_doc]
                mock_reader_class.return_value = mock_reader
                
                result = await parser_service.parse_document(tmp_path)
                
                assert result["metadata"]["author"] == "Test Author"
                assert result["metadata"]["title"] == "Test Strategy"
                assert result["metadata"]["creation_date"] == "2023-01-01"
                
        finally:
            os.unlink(tmp_path)
    
    async def test_parse_empty_file(self, parser_service):
        """Test parsing empty file."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            result = await parser_service.parse_document(tmp_path)
            
            assert result["success"] is True
            assert result["extracted_text"] == ""
            assert result["metadata"]["file_size"] == 0
            
        finally:
            os.unlink(tmp_path)
    
    async def test_parse_large_text_file(self, parser_service):
        """Test parsing large text file."""
        # Create a large text file (1MB)
        large_content = "Large strategy document. " * 50000
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as tmp:
            tmp.write(large_content)
            tmp_path = tmp.name
        
        try:
            result = await parser_service.parse_document(tmp_path)
            
            assert result["success"] is True
            assert len(result["extracted_text"]) > 1000000
            assert result["metadata"]["file_size"] > 1000000
            
        finally:
            os.unlink(tmp_path)