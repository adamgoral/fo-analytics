"""Document processing consumer/worker."""

import asyncio
import time
from typing import Optional

import aio_pika
import structlog
from aio_pika import IncomingMessage

from core.config import settings
from services.storage import StorageService
from services.document_parser import DocumentParserService
from services.llm import LLMService
from repositories.document import DocumentRepository
from db.session import get_db
from .connection import get_rabbitmq_connection
from .publisher import MessagePublisher
from .schemas import DocumentProcessingMessage, MessageStatus
from api.websockets import notifier

logger = structlog.get_logger(__name__)


class DocumentProcessingConsumer:
    """Consumes and processes document messages from RabbitMQ."""
    
    def __init__(self):
        self._connection = None
        self._publisher = MessagePublisher()
        self._storage_service = StorageService()
        self._parser_service = DocumentParserService()
        self._llm_service = LLMService()
        self._running = False
        
    async def start(self):
        """Start consuming messages."""
        self._running = True
        self._connection = await get_rabbitmq_connection()
        
        try:
            channel = await self._connection.get_channel()
            queue = await channel.get_queue(settings.rabbitmq_document_queue)
            
            logger.info("Starting document processing consumer")
            
            # Start consuming messages
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    if not self._running:
                        break
                        
                    try:
                        await self._process_message(message)
                    except Exception as e:
                        logger.error(
                            "Error processing message",
                            error=str(e),
                            message_id=message.message_id
                        )
                        
        except Exception as e:
            logger.error("Consumer error", error=str(e))
            raise
            
    async def stop(self):
        """Stop consuming messages."""
        self._running = False
        logger.info("Stopping document processing consumer")
        
    async def _process_message(self, message: IncomingMessage):
        """Process a single message."""
        start_time = time.time()
        
        try:
            # Parse message
            data = DocumentProcessingMessage.model_validate_json(message.body)
            
            logger.info(
                "Processing document",
                document_id=str(data.document_id),
                filename=data.filename,
                processing_type=data.processing_type
            )
            
            # Update document status to processing
            async for db in get_db():
                doc_repo = DocumentRepository(db)
                await doc_repo.update(
                    data.document_id,
                    {"status": "processing"}
                )
                await db.commit()
            
            # Send WebSocket notification
            await notifier.document_processing_started(
                user_id=str(data.user_id),
                document_id=str(data.document_id)
            )
            
            # Process based on type
            if data.processing_type == "parse_only":
                result = await self._parse_document(data)
            elif data.processing_type == "extract_only":
                result = await self._extract_strategies(data)
            else:  # full processing
                result = await self._full_processing(data)
                
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Publish success result
            await self._publisher.publish_processing_result(
                document_id=data.document_id,
                status=MessageStatus.COMPLETED,
                result=result,
                processing_time_ms=processing_time_ms,
                correlation_id=data.correlation_id
            )
            
            # Update document status to completed
            async for db in get_db():
                doc_repo = DocumentRepository(db)
                update_data = {
                    "status": "completed",
                    "processing_completed_at": time.time()
                }
                if "extracted_text" in result:
                    update_data["extracted_text"] = result["extracted_text"]
                if "strategies" in result:
                    update_data["extracted_strategies"] = result["strategies"]
                    
                await doc_repo.update(data.document_id, update_data)
                await db.commit()
            
            # Send WebSocket notification
            strategies_count = result.get("strategy_count", 0)
            await notifier.document_processing_completed(
                user_id=str(data.user_id),
                document_id=str(data.document_id),
                strategies_count=strategies_count
            )
            
            # Acknowledge message
            await message.ack()
            
            logger.info(
                "Document processed successfully",
                document_id=str(data.document_id),
                processing_time_ms=processing_time_ms
            )
            
        except Exception as e:
            logger.error(
                "Failed to process document",
                error=str(e),
                document_id=str(data.document_id) if 'data' in locals() else None
            )
            
            # Handle retry logic
            if 'data' in locals():
                await self._handle_failure(message, data, str(e))
            else:
                # Can't retry if we couldn't parse the message
                await message.reject(requeue=False)
                
    async def _parse_document(self, data: DocumentProcessingMessage) -> dict:
        """Parse document and extract text."""
        # Send progress notification
        await notifier.document_processing_progress(
            user_id=str(data.user_id),
            document_id=str(data.document_id),
            progress=0.2,
            message="Downloading document from storage"
        )
        
        # Download document from storage
        file_content = await self._storage_service.download_file(data.file_key)
        
        # Send progress notification
        await notifier.document_processing_progress(
            user_id=str(data.user_id),
            document_id=str(data.document_id),
            progress=0.4,
            message="Parsing document content"
        )
        
        # Parse document
        parsed_doc = await self._parser_service.parse_document(
            file_content,
            data.filename,
            data.content_type
        )
        
        return {
            "extracted_text": parsed_doc.text,
            "metadata": parsed_doc.metadata,
            "pages": len(parsed_doc.pages) if parsed_doc.pages else 1
        }
        
    async def _extract_strategies(self, data: DocumentProcessingMessage) -> dict:
        """Extract strategies from document text."""
        # Send progress notification
        await notifier.document_processing_progress(
            user_id=str(data.user_id),
            document_id=str(data.document_id),
            progress=0.6,
            message="Retrieving document text"
        )
        
        # Get document text from database
        async for db in get_db():
            doc_repo = DocumentRepository(db)
            document = await doc_repo.get(data.document_id)
            
            if not document or not document.extracted_text:
                raise ValueError("Document text not found")
                
            text = document.extracted_text
        
        # Send progress notification
        await notifier.document_processing_progress(
            user_id=str(data.user_id),
            document_id=str(data.document_id),
            progress=0.8,
            message="Analyzing document with AI to extract strategies"
        )
            
        # Extract strategies using LLM
        strategies = await self._llm_service.extract_strategies(text)
        
        # Send notification for each extracted strategy
        for i, strategy in enumerate(strategies):
            await notifier.strategy_extracted(
                user_id=str(data.user_id),
                document_id=str(data.document_id),
                strategy_id=f"{data.document_id}_strategy_{i}",
                strategy_name=strategy.get("name", f"Strategy {i+1}")
            )
        
        return {
            "strategies": strategies,
            "strategy_count": len(strategies)
        }
        
    async def _full_processing(self, data: DocumentProcessingMessage) -> dict:
        """Full document processing: parse and extract strategies."""
        # Parse document first
        parse_result = await self._parse_document(data)
        
        # Then extract strategies
        strategies = await self._llm_service.extract_strategies(
            parse_result["extracted_text"]
        )
        
        # Combine results
        return {
            **parse_result,
            "strategies": strategies,
            "strategy_count": len(strategies)
        }
        
    async def _handle_failure(
        self,
        message: IncomingMessage,
        data: DocumentProcessingMessage,
        error: str
    ):
        """Handle message processing failure."""
        try:
            # Update document status to failed
            async for db in get_db():
                doc_repo = DocumentRepository(db)
                await doc_repo.update(
                    data.document_id,
                    {
                        "status": "failed",
                        "error_message": error
                    }
                )
                await db.commit()
            
            # Send WebSocket notification
            await notifier.document_processing_failed(
                user_id=str(data.user_id),
                document_id=str(data.document_id),
                error=error
            )
            
            # Check retry count
            if data.retry_count < settings.rabbitmq_max_retries:
                # Publish retry message
                await self._publisher.publish_retry(data, error)
                await message.ack()  # Acknowledge original
            else:
                # Max retries exceeded, send to DLQ
                await message.reject(requeue=False)
                
                # Publish failure result
                await self._publisher.publish_processing_result(
                    document_id=data.document_id,
                    status=MessageStatus.FAILED,
                    error=f"Max retries exceeded: {error}",
                    correlation_id=data.correlation_id
                )
                
        except Exception as e:
            logger.error(
                "Failed to handle message failure",
                error=str(e),
                original_error=error
            )
            # Reject without requeue to send to DLQ
            await message.reject(requeue=False)


async def run_consumer():
    """Run the document processing consumer."""
    consumer = DocumentProcessingConsumer()
    
    try:
        await consumer.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await consumer.stop()


if __name__ == "__main__":
    # Run consumer directly
    asyncio.run(run_consumer())