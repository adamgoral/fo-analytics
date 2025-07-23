#!/usr/bin/env python
"""
Document processing worker.

This script runs the RabbitMQ consumer that processes documents
asynchronously. It should be run as a separate process from the
main API server.

Usage:
    python -m worker
    or
    uv run python -m worker
"""

import asyncio
import signal
import sys
from typing import Optional

from utils.logging import configure_logging, logger
from messaging.consumer import DocumentProcessingConsumer


class WorkerManager:
    """Manages the document processing worker lifecycle."""
    
    def __init__(self):
        self.consumer: Optional[DocumentProcessingConsumer] = None
        self._shutdown_event = asyncio.Event()
        
    def handle_signal(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self._shutdown_event.set()
        
    async def run(self):
        """Run the worker until shutdown signal is received."""
        # Configure logging
        configure_logging()
        logger.info("Starting document processing worker")
        
        # Create and start consumer
        self.consumer = DocumentProcessingConsumer()
        
        # Start consumer in background
        consumer_task = asyncio.create_task(self.consumer.start())
        
        # Wait for shutdown signal
        await self._shutdown_event.wait()
        
        # Stop consumer
        if self.consumer:
            await self.consumer.stop()
            
        # Cancel consumer task
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
            
        logger.info("Worker shutdown complete")


def main():
    """Main entry point for the worker."""
    # Create worker manager
    manager = WorkerManager()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, manager.handle_signal)
    signal.signal(signal.SIGTERM, manager.handle_signal)
    
    # Run the worker
    try:
        asyncio.run(manager.run())
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()