"""Tests for document parser service."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile
from io import BytesIO

from services.document_parser import DocumentParserService
from services.storage import StorageService
from schemas.document import DocumentMetadata


@pytest.fixture
def mock_storage_service():
    """Create a mock storage service."""
    service = Mock(spec=StorageService)
    service.download_file = AsyncMock()
    return service


@pytest.fixture
def parser_service(mock_storage_service):
    """Create a document parser service with mocked dependencies."""
    return DocumentParserService(mock_storage_service)


@pytest.mark.asyncio
async def test_parse_pdf_document(parser_service, mock_storage_service):
    """Test parsing a PDF document."""
    # Mock PDF content
    pdf_content = b"Mock PDF content"
    mock_storage_service.download_file.return_value = pdf_content
    
    # Mock LlamaIndex components
    with patch('services.document_parser.SimpleDirectoryReader') as mock_reader_class:
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.text = "This is extracted text from the PDF"
        mock_doc.metadata = {"page_label": "1"}
        
        # Configure mock reader
        mock_reader = MagicMock()
        mock_reader.load_data.return_value = [mock_doc]
        mock_reader_class.return_value = mock_reader
        
        # Parse document
        text, metadata = await parser_service.parse_document(
            user_id=1,
            file_key="test.pdf",
            extract_metadata=True
        )
        
        # Verify results
        assert text == "This is extracted text from the PDF"
        assert isinstance(metadata, DocumentMetadata)
        assert metadata.page_count == 1
        assert metadata.text_length == len(text)
        assert metadata.file_name == "test.pdf"
        
        # Verify download was called
        mock_storage_service.download_file.assert_called_once_with(1, "test.pdf")


@pytest.mark.asyncio
async def test_parse_unsupported_file_type(parser_service):
    """Test parsing an unsupported file type raises error."""
    with pytest.raises(ValueError, match="Unsupported file type: .xyz"):
        await parser_service.parse_document(
            user_id=1,
            file_key="test.xyz",
            extract_metadata=True
        )


@pytest.mark.asyncio
async def test_parse_document_by_pages(parser_service, mock_storage_service):
    """Test parsing document by pages."""
    # Mock PDF content
    pdf_content = b"Mock PDF content"
    mock_storage_service.download_file.return_value = pdf_content
    
    with patch('services.document_parser.SimpleDirectoryReader') as mock_reader_class:
        # Create mock documents for multiple pages
        mock_docs = []
        for i in range(3):
            mock_doc = MagicMock()
            mock_doc.text = f"Page {i + 1} content"
            mock_doc.metadata = {"page_label": str(i + 1)}
            mock_docs.append(mock_doc)
        
        # Configure mock reader
        mock_reader = MagicMock()
        mock_reader.load_data.return_value = mock_docs
        mock_reader_class.return_value = mock_reader
        
        # Parse document by pages
        pages = await parser_service.parse_document_by_pages(
            user_id=1,
            file_key="test.pdf"
        )
        
        # Verify results
        assert len(pages) == 3
        for i, page in enumerate(pages):
            assert page["page_number"] == i + 1
            assert page["text"] == f"Page {i + 1} content"
            assert page["text_length"] == len(page["text"])


@pytest.mark.asyncio
async def test_extract_metadata(parser_service):
    """Test metadata extraction from documents."""
    # Create mock documents
    mock_doc1 = MagicMock()
    mock_doc1.text = "First page"
    mock_doc1.metadata = {
        "page_label": "1",
        "author": "Test Author",
        "title": "Test Document"
    }
    
    mock_doc2 = MagicMock()
    mock_doc2.text = "Second page"
    mock_doc2.metadata = {"page_label": "2"}
    
    documents = [mock_doc1, mock_doc2]
    
    # Extract metadata
    metadata = parser_service._extract_metadata(documents, "test.pdf")
    
    # Verify results
    assert metadata.page_count == 2
    assert metadata.text_length == len("First page") + len("Second page")
    assert metadata.file_name == "test.pdf"


@pytest.mark.asyncio
async def test_parse_text_document(parser_service, mock_storage_service):
    """Test parsing a text document."""
    # Mock text content
    text_content = b"This is a plain text document"
    mock_storage_service.download_file.return_value = text_content
    
    with patch('services.document_parser.SimpleDirectoryReader') as mock_reader_class:
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.text = "This is a plain text document"
        mock_doc.metadata = {}
        
        # Configure mock reader
        mock_reader = MagicMock()
        mock_reader.load_data.return_value = [mock_doc]
        mock_reader_class.return_value = mock_reader
        
        # Parse document
        text, metadata = await parser_service.parse_document(
            user_id=1,
            file_key="test.txt",
            extract_metadata=True
        )
        
        # Verify results
        assert text == "This is a plain text document"
        assert metadata.page_count == 1
        assert metadata.file_name == "test.txt"


@pytest.mark.asyncio
async def test_parse_empty_document(parser_service, mock_storage_service):
    """Test parsing an empty document raises error."""
    # Mock empty content
    mock_storage_service.download_file.return_value = b""
    
    with patch('services.document_parser.SimpleDirectoryReader') as mock_reader_class:
        # Configure mock reader to return no documents
        mock_reader = MagicMock()
        mock_reader.load_data.return_value = []
        mock_reader_class.return_value = mock_reader
        
        # Attempt to parse document
        with pytest.raises(ValueError, match="No content extracted from document"):
            await parser_service.parse_document(
                user_id=1,
                file_key="empty.pdf",
                extract_metadata=True
            )


@pytest.mark.asyncio
async def test_extract_tables(parser_service, mock_storage_service):
    """Test table extraction from PDF."""
    # Mock PDF content
    pdf_content = b"Mock PDF content"
    mock_storage_service.download_file.return_value = pdf_content
    
    with patch('services.document_parser.SimpleDirectoryReader') as mock_reader_class:
        # Create mock document with table
        mock_doc = MagicMock()
        mock_doc.text = """
        | Column 1 | Column 2 |
        |----------|----------|
        | Data 1   | Data 2   |
        """
        mock_doc.metadata = {"page_label": "1"}
        
        # Configure mock reader
        mock_reader = MagicMock()
        mock_reader.load_data.return_value = [mock_doc]
        mock_reader_class.return_value = mock_reader
        
        # Extract tables
        with patch.object(parser_service, 'parse_document_by_pages') as mock_parse:
            mock_parse.return_value = [{
                "page_number": 1,
                "text": mock_doc.text,
                "metadata": mock_doc.metadata,
                "text_length": len(mock_doc.text)
            }]
            
            tables = await parser_service.extract_tables(
                user_id=1,
                file_key="table.pdf"
            )
            
            # Verify results
            assert len(tables) == 1
            assert tables[0]["page_number"] == 1
            assert "| Column 1 | Column 2 |" in tables[0]["table_text"]
            assert tables[0]["format"] == "markdown"


@pytest.mark.asyncio
async def test_extract_tables_non_pdf(parser_service):
    """Test table extraction from non-PDF returns empty list."""
    tables = await parser_service.extract_tables(
        user_id=1,
        file_key="document.txt"
    )
    
    assert tables == []


def test_get_supported_formats(parser_service):
    """Test getting supported file formats."""
    formats = parser_service.get_supported_formats()
    
    assert ".pdf" in formats
    assert ".txt" in formats
    assert ".md" in formats
    assert len(formats) == 3