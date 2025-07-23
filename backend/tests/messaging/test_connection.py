"""Tests for RabbitMQ connection manager."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aio_pika
from aio_pika import ExchangeType

from messaging.connection import RabbitMQConnection, get_rabbitmq_connection
from core.config import settings


class TestRabbitMQConnection:
    """Test RabbitMQConnection class."""
    
    @pytest.fixture
    def mock_connection(self):
        """Create mock RabbitMQ connection."""
        mock = AsyncMock(spec=aio_pika.RobustConnection)
        mock.is_closed = False
        return mock
    
    @pytest.fixture
    def mock_channel(self):
        """Create mock RabbitMQ channel."""
        mock = AsyncMock(spec=aio_pika.RobustChannel)
        mock.is_closed = False
        return mock
    
    @pytest.fixture
    def mock_exchange(self):
        """Create mock exchange."""
        return AsyncMock(spec=aio_pika.Exchange)
    
    @pytest.mark.asyncio
    async def test_connect_success(self, mock_connection, mock_channel, mock_exchange):
        """Test successful connection to RabbitMQ."""
        with patch("aio_pika.connect_robust", return_value=mock_connection):
            mock_connection.channel.return_value = mock_channel
            mock_channel.declare_exchange.return_value = mock_exchange
            mock_channel.declare_queue.return_value = AsyncMock()
            
            connection = RabbitMQConnection()
            await connection.connect()
            
            # Verify connection was established
            assert connection._connection == mock_connection
            assert connection._channel == mock_channel
            assert connection._exchange == mock_exchange
            
            # Verify exchange was declared
            mock_channel.declare_exchange.assert_called_once_with(
                settings.rabbitmq_exchange,
                type=ExchangeType.TOPIC,
                durable=True
            )
            
            # Verify queues were declared
            assert mock_channel.declare_queue.call_count == 2  # main + DLQ
    
    @pytest.mark.asyncio
    async def test_connect_already_connected(self, mock_connection, mock_channel):
        """Test connecting when already connected."""
        connection = RabbitMQConnection()
        connection._connection = mock_connection
        connection._channel = mock_channel
        
        with patch("aio_pika.connect_robust") as mock_connect:
            await connection.connect()
            
            # Should not attempt new connection
            mock_connect.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure handling."""
        with patch("aio_pika.connect_robust", side_effect=Exception("Connection failed")):
            connection = RabbitMQConnection()
            
            with pytest.raises(Exception, match="Connection failed"):
                await connection.connect()
            
            assert connection._connection is None
            assert connection._channel is None
    
    @pytest.mark.asyncio
    async def test_disconnect(self, mock_connection, mock_channel):
        """Test disconnecting from RabbitMQ."""
        connection = RabbitMQConnection()
        connection._connection = mock_connection
        connection._channel = mock_channel
        
        await connection.disconnect()
        
        mock_channel.close.assert_called_once()
        mock_connection.close.assert_called_once()
        
        assert connection._connection is None
        assert connection._channel is None
        assert connection._exchange is None
    
    @pytest.mark.asyncio
    async def test_disconnect_already_closed(self):
        """Test disconnecting when already disconnected."""
        connection = RabbitMQConnection()
        
        # Should not raise error
        await connection.disconnect()
    
    @pytest.mark.asyncio
    async def test_get_channel(self, mock_connection, mock_channel):
        """Test getting channel."""
        connection = RabbitMQConnection()
        connection._channel = mock_channel
        
        channel = await connection.get_channel()
        assert channel == mock_channel
    
    @pytest.mark.asyncio
    async def test_get_channel_reconnect(self, mock_connection, mock_channel):
        """Test getting channel triggers reconnect if needed."""
        connection = RabbitMQConnection()
        
        with patch.object(connection, "connect") as mock_connect:
            await connection.get_channel()
            mock_connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_exchange(self, mock_exchange):
        """Test getting exchange."""
        connection = RabbitMQConnection()
        connection._exchange = mock_exchange
        
        exchange = await connection.get_exchange()
        assert exchange == mock_exchange
    
    def test_is_connected(self, mock_connection, mock_channel):
        """Test connection status check."""
        connection = RabbitMQConnection()
        
        # Not connected
        assert not connection.is_connected
        
        # Connected
        connection._connection = mock_connection
        connection._channel = mock_channel
        assert connection.is_connected
        
        # Connection closed
        mock_connection.is_closed = True
        assert not connection.is_connected
        
        # Channel closed
        mock_connection.is_closed = False
        mock_channel.is_closed = True
        assert not connection.is_connected


class TestGetRabbitMQConnection:
    """Test get_rabbitmq_connection function."""
    
    @pytest.mark.asyncio
    async def test_get_connection_singleton(self):
        """Test that connection is a singleton."""
        with patch("messaging.connection._rabbitmq_connection", None):
            with patch.object(RabbitMQConnection, "connect") as mock_connect:
                conn1 = await get_rabbitmq_connection()
                conn2 = await get_rabbitmq_connection()
                
                # Should be the same instance
                assert conn1 is conn2
                
                # Connect should only be called once
                mock_connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_connection_creates_new(self):
        """Test that new connection is created if none exists."""
        with patch("messaging.connection._rabbitmq_connection", None):
            with patch.object(RabbitMQConnection, "connect") as mock_connect:
                connection = await get_rabbitmq_connection()
                
                assert isinstance(connection, RabbitMQConnection)
                mock_connect.assert_called_once()