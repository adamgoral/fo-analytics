"""Consumer for processing backtest messages."""

import asyncio
import json
from typing import Optional
import structlog
from aio_pika import IncomingMessage

from core.database import get_async_session
from repositories.unit_of_work import UnitOfWork
from services.backtesting import BacktestingService
from websocket_manager import WebSocketNotifier
from .connection import get_connection_manager
from .schemas import ProcessingMode
from .backtest_schemas import BacktestMessage

logger = structlog.get_logger(__name__)


class BacktestConsumer:
    """Consumes backtest messages from RabbitMQ and processes them."""
    
    def __init__(self):
        self.connection_manager = get_connection_manager()
        self.notifier = WebSocketNotifier()
        self.processing = False
    
    async def start(self) -> None:
        """Start consuming messages from the backtest queue."""
        try:
            await self.connection_manager.connect()
            channel = await self.connection_manager.get_channel()
            
            # Declare backtest queue
            queue = await channel.declare_queue(
                "backtest_processing",
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "",
                    "x-dead-letter-routing-key": "backtest_processing_dlq"
                }
            )
            
            # Declare dead letter queue
            await channel.declare_queue(
                "backtest_processing_dlq",
                durable=True
            )
            
            # Set QoS
            await channel.set_qos(prefetch_count=1)
            
            # Start consuming
            self.processing = True
            await queue.consume(self._process_message)
            
            logger.info("Backtest consumer started")
            
            # Keep the consumer running
            while self.processing:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error("Error in backtest consumer", error=str(e))
            raise
        finally:
            await self.connection_manager.disconnect()
    
    async def stop(self) -> None:
        """Stop the consumer."""
        self.processing = False
        logger.info("Backtest consumer stopping")
    
    async def _process_message(self, message: IncomingMessage) -> None:
        """Process a single backtest message."""
        async with message.process():
            try:
                # Parse message
                body = json.loads(message.body.decode())
                backtest_msg = BacktestMessage(**body)
                
                logger.info(
                    "Processing backtest",
                    backtest_id=backtest_msg.backtest_id,
                    strategy_id=backtest_msg.strategy_id
                )
                
                # Process backtest
                await self._execute_backtest(backtest_msg)
                
                # Acknowledge message
                await message.ack()
                
            except Exception as e:
                logger.error(
                    "Error processing backtest message",
                    error=str(e),
                    traceback=True
                )
                
                # Check retry count
                retry_count = message.headers.get("x-retry-count", 0)
                if retry_count < 3:
                    # Retry with exponential backoff
                    await self._retry_message(message, retry_count + 1)
                else:
                    # Send to DLQ
                    await message.nack(requeue=False)
                    logger.error(
                        "Message sent to DLQ after max retries",
                        retry_count=retry_count
                    )
    
    async def _execute_backtest(self, msg: BacktestMessage) -> None:
        """Execute the backtest using the backtesting service."""
        # Get database session
        async for session in get_async_session():
            uow = UnitOfWork(session)
            service = BacktestingService(uow)
            
            try:
                # Send initial notification
                await self.notifier.send_backtest_notification(
                    msg.backtest_id,
                    "started",
                    "Backtest execution started",
                    progress=0
                )
                
                # Get strategy
                async with uow:
                    strategy = await uow.strategies.get(msg.strategy_id)
                    if not strategy:
                        raise ValueError(f"Strategy {msg.strategy_id} not found")
                
                # Run backtest
                results = await service.run_backtest(msg.backtest_id, strategy)
                
                # Send completion notification
                await self.notifier.send_backtest_notification(
                    msg.backtest_id,
                    "completed",
                    "Backtest completed successfully",
                    progress=100,
                    results=results
                )
                
                logger.info(
                    "Backtest completed",
                    backtest_id=msg.backtest_id,
                    total_return=results.get("total_return")
                )
                
            except Exception as e:
                # Send error notification
                await self.notifier.send_backtest_notification(
                    msg.backtest_id,
                    "failed",
                    f"Backtest failed: {str(e)}",
                    progress=0
                )
                raise
            
            finally:
                # Ensure session is closed
                await session.close()
    
    async def _retry_message(
        self,
        message: IncomingMessage,
        retry_count: int
    ) -> None:
        """Retry a message with exponential backoff."""
        delay = min(300, 10 * (2 ** (retry_count - 1)))  # Max 5 minutes
        
        logger.info(
            "Retrying message",
            retry_count=retry_count,
            delay=delay
        )
        
        # Re-publish with retry count and delay
        channel = await self.connection_manager.get_channel()
        
        # Add retry count to headers
        headers = dict(message.headers or {})
        headers["x-retry-count"] = retry_count
        
        # Publish with delay using delayed message plugin or TTL
        await channel.default_exchange.publish(
            message,
            routing_key=message.routing_key or "backtest_processing",
            headers=headers
        )
        
        # Acknowledge original message
        await message.ack()


async def run_backtest_consumer():
    """Run the backtest consumer."""
    consumer = BacktestConsumer()
    try:
        await consumer.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(run_backtest_consumer())