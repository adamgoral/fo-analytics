"""Tests for backtest execution message publishing."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from src.messaging.publisher import MessagePublisher
from src.messaging.schemas import BacktestExecutionMessage


@pytest.mark.asyncio
class TestBacktestPublisher:
    """Test backtest execution message publishing."""
    
    @pytest.fixture
    def mock_connection(self):
        """Create a mock RabbitMQ connection."""
        connection = Mock()
        exchange = AsyncMock()
        connection.get_exchange = AsyncMock(return_value=exchange)
        return connection, exchange
    
    @pytest.fixture
    def publisher(self):
        """Create a message publisher instance."""
        return MessagePublisher()
    
    async def test_publish_backtest_execution_success(self, publisher, mock_connection):
        """Test successful backtest execution message publishing."""
        connection, exchange = mock_connection
        
        # Mock the connection
        with patch('src.messaging.publisher.get_rabbitmq_connection', return_value=connection):
            # Test data
            backtest_id = 1
            user_id = uuid4()
            strategy_id = 1
            strategy_name = "Test Strategy"
            strategy_code = "def backtest(): pass"
            parameters = {
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "initial_capital": 100000
            }
            
            # Publish message
            message_id = await publisher.publish_backtest_execution(
                backtest_id=backtest_id,
                user_id=user_id,
                strategy_id=strategy_id,
                strategy_name=strategy_name,
                strategy_code=strategy_code,
                parameters=parameters
            )
            
            # Verify message was published
            assert message_id is not None
            exchange.publish.assert_called_once()
            
            # Verify message content
            published_call = exchange.publish.call_args
            message = published_call[0][0]
            assert message.content_type == "application/json"
            assert message.delivery_mode.value == 2  # Persistent
            
            # Verify routing key
            assert published_call[1]["routing_key"] == "backtest.execute"
    
    async def test_publish_backtest_execution_with_correlation_id(self, publisher, mock_connection):
        """Test backtest execution message publishing with correlation ID."""
        connection, exchange = mock_connection
        
        with patch('src.messaging.publisher.get_rabbitmq_connection', return_value=connection):
            correlation_id = uuid4()
            
            message_id = await publisher.publish_backtest_execution(
                backtest_id=1,
                user_id=uuid4(),
                strategy_id=1,
                strategy_name="Test Strategy",
                strategy_code="def backtest(): pass",
                parameters={"initial_capital": 100000},
                correlation_id=correlation_id
            )
            
            # Verify correlation ID was set
            published_call = exchange.publish.call_args
            message = published_call[0][0]
            assert message.correlation_id == str(correlation_id)
    
    async def test_publish_backtest_execution_connection_error(self, publisher):
        """Test backtest execution message publishing with connection error."""
        with patch('src.messaging.publisher.get_rabbitmq_connection', side_effect=Exception("Connection failed")):
            
            with pytest.raises(Exception) as exc_info:
                await publisher.publish_backtest_execution(
                    backtest_id=1,
                    user_id=uuid4(),
                    strategy_id=1,
                    strategy_name="Test Strategy",
                    strategy_code="def backtest(): pass",
                    parameters={}
                )
            
            assert "Connection failed" in str(exc_info.value)
    
    async def test_publish_backtest_execution_publish_error(self, publisher, mock_connection):
        """Test backtest execution message publishing with publish error."""
        connection, exchange = mock_connection
        exchange.publish.side_effect = Exception("Publish failed")
        
        with patch('src.messaging.publisher.get_rabbitmq_connection', return_value=connection):
            
            with pytest.raises(Exception) as exc_info:
                await publisher.publish_backtest_execution(
                    backtest_id=1,
                    user_id=uuid4(),
                    strategy_id=1,
                    strategy_name="Test Strategy",
                    strategy_code="def backtest(): pass",
                    parameters={}
                )
            
            assert "Publish failed" in str(exc_info.value)