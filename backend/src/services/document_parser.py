"""Document parsing service using LlamaIndex for text extraction."""
import os
import tempfile
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import aiofiles
from llama_index.core import SimpleDirectoryReader
from llama_index.readers.file import PDFReader, PyMuPDFReader
from llama_index.core.schema import Document as LlamaDocument

from utils.logging import logger
from services.storage import StorageService
from schemas.document import DocumentMetadata


class DocumentParserService:
    """Service for parsing documents and extracting text using LlamaIndex."""
    
    def __init__(self, storage_service: StorageService):
        """Initialize document parser service.
        
        Args:
            storage_service: Service for accessing document storage
        """
        self.storage_service = storage_service
        
        # Configure file extractors for different document types
        self.file_extractors = {
            ".pdf": PyMuPDFReader(),  # Better for complex PDFs with tables/formatting
            ".txt": None,  # SimpleDirectoryReader handles text files natively
            ".md": None,   # SimpleDirectoryReader handles markdown natively
        }
        
    async def parse_document(
        self, 
        user_id: int, 
        file_key: str,
        extract_metadata: bool = True
    ) -> Tuple[str, Optional[DocumentMetadata]]:
        """Parse a document from storage and extract text content.
        
        Args:
            user_id: ID of the user who owns the document
            file_key: Storage key of the document
            extract_metadata: Whether to extract document metadata
            
        Returns:
            Tuple of (extracted_text, metadata)
            
        Raises:
            ValueError: If document type is not supported
            Exception: If parsing fails
        """
        file_ext = Path(file_key).suffix.lower()
        
        # Check if file type is supported
        if file_ext not in self.file_extractors:
            raise ValueError(f"Unsupported file type: {file_ext}")
            
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_filename = Path(file_key).name
            temp_path = Path(temp_dir) / temp_filename
            
            try:
                # Download file from storage to temporary location
                logger.info(
                    "Downloading document for parsing",
                    user_id=user_id,
                    file_key=file_key
                )
                
                file_data, _ = await self.storage_service.download_file(file_key)
                
                # Write to temporary file
                async with aiofiles.open(temp_path, 'wb') as f:
                    await f.write(file_data)
                
                # Parse document using LlamaIndex
                logger.info(
                    "Parsing document",
                    file_path=str(temp_path),
                    file_type=file_ext
                )
                
                # Use SimpleDirectoryReader with custom extractors only for files that need them
                if file_ext in self.file_extractors and self.file_extractors[file_ext] is not None:
                    reader = SimpleDirectoryReader(
                        input_files=[str(temp_path)],
                        file_extractor=self.file_extractors,
                        filename_as_id=True
                    )
                else:
                    # Use default reader for text files
                    reader = SimpleDirectoryReader(
                        input_files=[str(temp_path)],
                        filename_as_id=True
                    )
                
                documents = reader.load_data()
                
                if not documents:
                    raise ValueError("No content extracted from document")
                
                # Combine text from all document chunks
                extracted_text = "\n\n".join(doc.text for doc in documents)
                
                # Extract metadata if requested
                metadata = None
                if extract_metadata:
                    metadata = self._extract_metadata(documents, file_key)
                
                logger.info(
                    "Document parsed successfully",
                    user_id=user_id,
                    file_key=file_key,
                    text_length=len(extracted_text),
                    num_pages=len(documents)
                )
                
                return extracted_text, metadata
                
            except Exception as e:
                logger.error(
                    "Failed to parse document",
                    user_id=user_id,
                    file_key=file_key,
                    error=str(e)
                )
                raise
                
    async def parse_document_by_pages(
        self,
        user_id: int,
        file_key: str
    ) -> List[Dict[str, any]]:
        """Parse document and return content by pages.
        
        Args:
            user_id: ID of the user who owns the document
            file_key: Storage key of the document
            
        Returns:
            List of dictionaries containing page content and metadata
        """
        file_ext = Path(file_key).suffix.lower()
        
        if file_ext not in self.file_extractors:
            raise ValueError(f"Unsupported file type: {file_ext}")
            
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_filename = Path(file_key).name
            temp_path = Path(temp_dir) / temp_filename
            
            try:
                # Download file
                file_data, _ = await self.storage_service.download_file(file_key)
                
                async with aiofiles.open(temp_path, 'wb') as f:
                    await f.write(file_data)
                
                # Parse with page separation
                if file_ext == ".pdf":
                    # Use PDFReader with return_full_document=False for page separation
                    pdf_reader = PDFReader(return_full_document=False)
                    reader = SimpleDirectoryReader(
                        input_files=[str(temp_path)],
                        file_extractor={".pdf": pdf_reader}
                    )
                elif file_ext in self.file_extractors and self.file_extractors[file_ext] is not None:
                    reader = SimpleDirectoryReader(
                        input_files=[str(temp_path)],
                        file_extractor=self.file_extractors
                    )
                else:
                    # Use default reader
                    reader = SimpleDirectoryReader(
                        input_files=[str(temp_path)]
                    )
                
                documents = reader.load_data()
                
                # Format pages
                pages = []
                for i, doc in enumerate(documents):
                    page_data = {
                        "page_number": i + 1,
                        "text": doc.text,
                        "metadata": doc.metadata,
                        "text_length": len(doc.text)
                    }
                    pages.append(page_data)
                
                logger.info(
                    "Document parsed by pages",
                    user_id=user_id,
                    file_key=file_key,
                    num_pages=len(pages)
                )
                
                return pages
                
            except Exception as e:
                logger.error(
                    "Failed to parse document by pages",
                    user_id=user_id,
                    file_key=file_key,
                    error=str(e)
                )
                raise
                
    def _extract_metadata(
        self, 
        documents: List[LlamaDocument], 
        file_key: str
    ) -> DocumentMetadata:
        """Extract metadata from parsed documents.
        
        Args:
            documents: List of LlamaIndex documents
            file_key: Original file key
            
        Returns:
            DocumentMetadata object
        """
        # Get metadata from first document (usually contains file-level metadata)
        first_doc_metadata = documents[0].metadata if documents else {}
        
        # Calculate total text length
        total_text_length = sum(len(doc.text) for doc in documents)
        
        # Extract page count
        page_count = len(documents)
        
        # Build metadata object
        metadata = DocumentMetadata(
            page_count=page_count,
            text_length=total_text_length,
            file_name=Path(file_key).name,
            # Additional metadata from LlamaIndex if available
            **{k: v for k, v in first_doc_metadata.items() 
               if k not in ['page_label', 'file_name', 'file_path']}
        )
        
        return metadata
        
    async def extract_tables(
        self,
        user_id: int,
        file_key: str
    ) -> List[Dict[str, any]]:
        """Extract tables from document (primarily PDFs).
        
        Args:
            user_id: ID of the user who owns the document
            file_key: Storage key of the document
            
        Returns:
            List of extracted tables as dictionaries
        """
        file_ext = Path(file_key).suffix.lower()
        
        if file_ext != ".pdf":
            logger.warning(
                "Table extraction only supported for PDFs",
                file_type=file_ext
            )
            return []
            
        # PyMuPDFReader can extract tables in markdown format
        # which can be parsed for structured data
        pages = await self.parse_document_by_pages(user_id, file_key)
        
        tables = []
        for page in pages:
            # Look for markdown tables in the text
            # This is a simple implementation - could be enhanced
            # with more sophisticated table detection
            text = page["text"]
            if "|" in text and "---" in text:
                # Likely contains a markdown table
                tables.append({
                    "page_number": page["page_number"],
                    "table_text": text,
                    "format": "markdown"
                })
                
        return tables
        
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats.
        
        Returns:
            List of supported file extensions
        """
        return list(self.file_extractors.keys())