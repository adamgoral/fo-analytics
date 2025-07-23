"""RabbitMQ connection management."""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

import aio_pika
from aio_pika import RobustConnection, RobustChannel, ExchangeType
import structlog

from core.config import settings

logger = structlog.get_logger(__name__)


class RabbitMQConnection:
    """Manages RabbitMQ connection and channel lifecycle."""
    
    def __init__(self):
        self._connection: Optional[RobustConnection] = None
        self._channel: Optional[RobustChannel] = None
        self._exchange: Optional[aio_pika.Exchange] = None
        self._lock = asyncio.Lock()
        
    async def connect(self) -> None:
        """Establish connection to RabbitMQ."""
        async with self._lock:
            if self._connection and not self._connection.is_closed:
                return
                
            try:
                logger.info("Connecting to RabbitMQ", url=settings.rabbitmq_url)
                
                # Create robust connection that automatically reconnects
                self._connection = await aio_pika.connect_robust(
                    settings.rabbitmq_url,
                    connection_name="fo-analytics-backend"
                )
                
                # Create channel
                self._channel = await self._connection.channel()
                await self._channel.set_qos(prefetch_count=settings.rabbitmq_prefetch_count)
                
                # Declare exchange
                self._exchange = await self._channel.declare_exchange(
                    settings.rabbitmq_exchange,
                    type=ExchangeType.TOPIC,
                    durable=True
                )
                
                # Declare main processing queue
                main_queue = await self._channel.declare_queue(
                    settings.rabbitmq_document_queue,
                    durable=True,
                    arguments={
                        "x-dead-letter-exchange": "",
                        "x-dead-letter-routing-key": settings.rabbitmq_dead_letter_queue,
                        "x-message-ttl": 3600000,  # 1 hour TTL
                    }
                )
                
                # Declare dead letter queue
                dlq = await self._channel.declare_queue(
                    settings.rabbitmq_dead_letter_queue,
                    durable=True,
                    arguments={
                        "x-message-ttl": 86400000,  # 24 hour TTL for dead letters
                    }
                )
                
                # Bind queues to exchange
                await main_queue.bind(self._exchange, routing_key="document.process")
                await dlq.bind(self._exchange, routing_key="document.failed")
                
                logger.info("Successfully connected to RabbitMQ")
                
            except Exception as e:
                logger.error("Failed to connect to RabbitMQ", error=str(e))
                raise
                
    async def disconnect(self) -> None:
        """Close RabbitMQ connection."""
        async with self._lock:
            if self._channel and not self._channel.is_closed:
                await self._channel.close()
                
            if self._connection and not self._connection.is_closed:
                await self._connection.close()
                
            self._connection = None
            self._channel = None
            self._exchange = None
            
            logger.info("Disconnected from RabbitMQ")
            
    async def get_channel(self) -> RobustChannel:
        """Get the current channel, connecting if necessary."""
        if not self._channel or self._channel.is_closed:
            await self.connect()
        return self._channel
        
    async def get_exchange(self) -> aio_pika.Exchange:
        """Get the current exchange, connecting if necessary."""
        if not self._exchange:
            await self.connect()
        return self._exchange
        
    @property
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return (
            self._connection is not None 
            and not self._connection.is_closed
            and self._channel is not None
            and not self._channel.is_closed
        )


# Global connection instance
_rabbitmq_connection: Optional[RabbitMQConnection] = None


async def get_rabbitmq_connection() -> RabbitMQConnection:
    """Get or create the global RabbitMQ connection."""
    global _rabbitmq_connection
    
    if _rabbitmq_connection is None:
        _rabbitmq_connection = RabbitMQConnection()
        await _rabbitmq_connection.connect()
        
    return _rabbitmq_connection


@asynccontextmanager
async def rabbitmq_context():
    """Context manager for RabbitMQ connection lifecycle."""
    connection = await get_rabbitmq_connection()
    try:
        yield connection
    finally:
        # Connection cleanup handled by app shutdown
        pass