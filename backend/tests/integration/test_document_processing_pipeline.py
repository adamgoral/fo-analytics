"""Integration tests for the complete document processing pipeline."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from io import BytesIO

from messaging.consumer import DocumentProcessingConsumer
from messaging.publisher import MessagePublisher
from messaging.schemas import DocumentProcessingMessage, MessageStatus
from services.storage import StorageService
from services.document_parser import DocumentParserService
from services.llm import LLMService
from models.document import DocumentStatus


@pytest.mark.asyncio
class TestDocumentProcessingPipeline:
    """Integration tests for document processing pipeline."""
    
    @pytest.fixture
    def mock_storage_service(self):
        """Mock storage service."""
        mock = AsyncMock(spec=StorageService)
        mock.download_file = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_parser_service(self):
        """Mock parser service."""
        mock = AsyncMock(spec=DocumentParserService)
        mock.parse_document = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service."""
        mock = AsyncMock(spec=LLMService)
        mock.extract_strategies = AsyncMock()
        return mock
    
    @pytest.fixture
    def sample_document_content(self):
        """Sample document content."""
        return b"""
Investment Strategy Document

Strategy 1: Growth Equity
- Focus on high-growth tech companies
- Target 25% annual returns
- Risk level: High

Strategy 2: Fixed Income
- Government and corporate bonds
- Target 5-7% annual returns
- Risk level: Low

Strategy 3: Balanced Portfolio
- Mix of equity and bonds
- Target 12% annual returns
- Risk level: Medium
"""
    
    async def test_full_document_processing_pipeline(
        self,
        mock_storage_service,
        mock_parser_service,
        mock_llm_service,
        sample_document_content
    ):
        """Test complete document processing from upload to strategy extraction."""
        # Setup mocks
        mock_storage_service.download_file.return_value = sample_document_content
        
        parsed_doc = MagicMock()
        parsed_doc.text = sample_document_content.decode()
        parsed_doc.metadata = {"pages": 1, "title": "Investment Strategy"}
        parsed_doc.pages = ["page1"]
        mock_parser_service.parse_document.return_value = parsed_doc
        
        mock_llm_service.extract_strategies.return_value = [
            {
                "name": "Growth Equity",
                "description": "Focus on high-growth tech companies",
                "target_return": "25%",
                "risk_level": "High"
            },
            {
                "name": "Fixed Income",
                "description": "Government and corporate bonds",
                "target_return": "5-7%",
                "risk_level": "Low"
            },
            {
                "name": "Balanced Portfolio",
                "description": "Mix of equity and bonds",
                "target_return": "12%",
                "risk_level": "Medium"
            }
        ]
        
        # Create consumer with mocked services
        consumer = DocumentProcessingConsumer()
        consumer._storage_service = mock_storage_service
        consumer._parser_service = mock_parser_service
        consumer._llm_service = mock_llm_service
        
        # Create test message
        message = DocumentProcessingMessage(
            message_id=uuid4(),
            document_id=uuid4(),
            user_id=uuid4(),
            file_key="user123/strategy_doc.pdf",
            filename="investment_strategy.pdf",
            file_size=len(sample_document_content),
            content_type="application/pdf",
            processing_type="full"
        )
        
        # Mock database operations
        with patch("messaging.consumer.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]
            mock_db.commit = AsyncMock()
            
            mock_doc_repo = AsyncMock()
            mock_doc_repo.update = AsyncMock()
            
            with patch("messaging.consumer.DocumentRepository", return_value=mock_doc_repo):
                # Mock publisher for result
                mock_publisher = AsyncMock()
                mock_publisher.publish_processing_result = AsyncMock()
                consumer._publisher = mock_publisher
                
                # Create mock incoming message
                mock_incoming_message = AsyncMock()
                mock_incoming_message.body = message.model_dump_json().encode()
                mock_incoming_message.message_id = str(message.message_id)
                mock_incoming_message.ack = AsyncMock()
                
                # Process message
                await consumer._process_message(mock_incoming_message)
        
        # Verify all services were called
        mock_storage_service.download_file.assert_called_once_with(message.file_key)
        mock_parser_service.parse_document.assert_called_once()
        mock_llm_service.extract_strategies.assert_called_once_with(parsed_doc.text)
        
        # Verify document was updated with processing status
        assert mock_doc_repo.update.call_count >= 2
        first_update = mock_doc_repo.update.call_args_list[0]
        assert first_update[0][1]["status"] == "processing"
        
        # Verify result was published
        mock_publisher.publish_processing_result.assert_called_once()
        result_args = mock_publisher.publish_processing_result.call_args[1]
        assert result_args["status"] == MessageStatus.COMPLETED
        assert result_args["result"]["extracted_text"] == parsed_doc.text
        assert len(result_args["result"]["strategies"]) == 3
        assert result_args["result"]["strategy_count"] == 3
        
        # Verify message was acknowledged
        mock_incoming_message.ack.assert_called_once()
    
    async def test_pipeline_with_parsing_error(
        self,
        mock_storage_service,
        mock_parser_service,
        sample_document_content
    ):
        """Test pipeline handling of parsing errors."""
        # Setup storage mock
        mock_storage_service.download_file.return_value = sample_document_content
        
        # Mock parser to fail
        mock_parser_service.parse_document.side_effect = Exception("Invalid PDF structure")
        
        # Create consumer
        consumer = DocumentProcessingConsumer()
        consumer._storage_service = mock_storage_service
        consumer._parser_service = mock_parser_service
        
        # Create test message
        message = DocumentProcessingMessage(
            message_id=uuid4(),
            document_id=uuid4(),
            user_id=uuid4(),
            file_key="user123/corrupt.pdf",
            filename="corrupt.pdf",
            file_size=1000,
            content_type="application/pdf",
            processing_type="parse_only"
        )
        
        # Mock database and publisher
        with patch("messaging.consumer.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]
            mock_db.commit = AsyncMock()
            
            mock_doc_repo = AsyncMock()
            mock_doc_repo.update = AsyncMock()
            
            with patch("messaging.consumer.DocumentRepository", return_value=mock_doc_repo):
                mock_publisher = AsyncMock()
                mock_publisher.publish_retry = AsyncMock()
                consumer._publisher = mock_publisher
                
                mock_incoming_message = AsyncMock()
                mock_incoming_message.body = message.model_dump_json().encode()
                mock_incoming_message.ack = AsyncMock()
                
                await consumer._process_message(mock_incoming_message)
        
        # Verify retry was published
        mock_publisher.publish_retry.assert_called_once()
        retry_args = mock_publisher.publish_retry.call_args[0]
        assert "Invalid PDF structure" in retry_args[1]
        
        # Verify document status was updated to failed
        fail_update = [call for call in mock_doc_repo.update.call_args_list 
                      if call[0][1].get("status") == "failed"]
        assert len(fail_update) > 0
    
    async def test_pipeline_with_llm_error(
        self,
        mock_storage_service,
        mock_parser_service,
        mock_llm_service,
        sample_document_content
    ):
        """Test pipeline handling of LLM extraction errors."""
        # Setup mocks
        mock_storage_service.download_file.return_value = sample_document_content
        
        parsed_doc = MagicMock()
        parsed_doc.text = sample_document_content.decode()
        parsed_doc.metadata = {"pages": 1}
        parsed_doc.pages = ["page1"]
        mock_parser_service.parse_document.return_value = parsed_doc
        
        # Mock LLM to fail
        mock_llm_service.extract_strategies.side_effect = Exception("LLM API rate limit exceeded")
        
        # Create consumer
        consumer = DocumentProcessingConsumer()
        consumer._storage_service = mock_storage_service
        consumer._parser_service = mock_parser_service
        consumer._llm_service = mock_llm_service
        
        # Create test message with retry count
        message = DocumentProcessingMessage(
            message_id=uuid4(),
            document_id=uuid4(),
            user_id=uuid4(),
            file_key="user123/doc.pdf",
            filename="doc.pdf",
            file_size=1000,
            content_type="application/pdf",
            processing_type="full",
            retry_count=1
        )
        
        # Mock database and publisher
        with patch("messaging.consumer.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]
            mock_db.commit = AsyncMock()
            
            mock_doc_repo = AsyncMock()
            mock_doc_repo.update = AsyncMock()
            
            with patch("messaging.consumer.DocumentRepository", return_value=mock_doc_repo):
                mock_publisher = AsyncMock()
                mock_publisher.publish_retry = AsyncMock()
                consumer._publisher = mock_publisher
                
                mock_incoming_message = AsyncMock()
                mock_incoming_message.body = message.model_dump_json().encode()
                mock_incoming_message.ack = AsyncMock()
                
                await consumer._process_message(mock_incoming_message)
        
        # Verify services were called up to the failure point
        mock_storage_service.download_file.assert_called_once()
        mock_parser_service.parse_document.assert_called_once()
        mock_llm_service.extract_strategies.assert_called_once()
        
        # Verify retry was published (since retry_count < max)
        mock_publisher.publish_retry.assert_called_once()
        
        # Message should still be acknowledged
        mock_incoming_message.ack.assert_called_once()
    
    async def test_pipeline_extract_only_mode(
        self,
        mock_llm_service
    ):
        """Test pipeline in extract-only mode (document already parsed)."""
        # Mock LLM response
        mock_llm_service.extract_strategies.return_value = [
            {"name": "Strategy A", "allocation": "50%"},
            {"name": "Strategy B", "allocation": "50%"}
        ]
        
        # Create consumer
        consumer = DocumentProcessingConsumer()
        consumer._llm_service = mock_llm_service
        
        # Create test message
        message = DocumentProcessingMessage(
            message_id=uuid4(),
            document_id=uuid4(),
            user_id=uuid4(),
            file_key="user123/parsed.pdf",
            filename="parsed.pdf",
            file_size=2000,
            content_type="application/pdf",
            processing_type="extract_only"
        )
        
        # Mock database with existing parsed document
        mock_document = MagicMock()
        mock_document.extracted_text = "This is the parsed document text with strategies."
        
        with patch("messaging.consumer.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]
            mock_db.commit = AsyncMock()
            
            mock_doc_repo = AsyncMock()
            mock_doc_repo.get = AsyncMock(return_value=mock_document)
            mock_doc_repo.update = AsyncMock()
            
            with patch("messaging.consumer.DocumentRepository", return_value=mock_doc_repo):
                mock_publisher = AsyncMock()
                mock_publisher.publish_processing_result = AsyncMock()
                consumer._publisher = mock_publisher
                
                mock_incoming_message = AsyncMock()
                mock_incoming_message.body = message.model_dump_json().encode()
                mock_incoming_message.ack = AsyncMock()
                
                await consumer._process_message(mock_incoming_message)
        
        # Verify document was fetched
        mock_doc_repo.get.assert_called_once_with(message.document_id)
        
        # Verify LLM was called with existing text
        mock_llm_service.extract_strategies.assert_called_once_with(mock_document.extracted_text)
        
        # Verify result was published
        mock_publisher.publish_processing_result.assert_called_once()
        result_args = mock_publisher.publish_processing_result.call_args[1]
        assert result_args["status"] == MessageStatus.COMPLETED
        assert len(result_args["result"]["strategies"]) == 2