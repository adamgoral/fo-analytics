"""Tests for WebSocket functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import WebSocket
from uuid import uuid4

from api.websockets import ConnectionManager, WebSocketNotifier, manager, notifier


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        self.accept = AsyncMock()
        self.send_json = AsyncMock()
        self.close = AsyncMock()
        self.client = MagicMock()
        self.client.host = "testhost"
        self.client.port = 12345


@pytest.mark.asyncio
class TestConnectionManager:
    """Test ConnectionManager functionality."""
    
    async def test_connect(self):
        """Test connecting a new WebSocket client."""
        cm = ConnectionManager()
        ws = MockWebSocket()
        client_id = "test-client-1"
        user_id = "test-user-1"
        
        await cm.connect(ws, client_id, user_id)
        
        ws.accept.assert_called_once()
        assert client_id in cm.active_connections
        assert cm.active_connections[client_id] == ws
        assert user_id in cm.user_connections
        assert client_id in cm.user_connections[user_id]
    
    async def test_disconnect(self):
        """Test disconnecting a WebSocket client."""
        cm = ConnectionManager()
        ws = MockWebSocket()
        client_id = "test-client-1"
        user_id = "test-user-1"
        
        # First connect
        await cm.connect(ws, client_id, user_id)
        
        # Then disconnect
        cm.disconnect(client_id, user_id)
        
        assert client_id not in cm.active_connections
        assert user_id not in cm.user_connections
    
    async def test_disconnect_removes_user_when_no_connections(self):
        """Test that user is removed when all connections are closed."""
        cm = ConnectionManager()
        ws = MockWebSocket()
        client_id = "test-client-1"
        user_id = "test-user-1"
        
        await cm.connect(ws, client_id, user_id)
        cm.disconnect(client_id, user_id)
        
        assert user_id not in cm.user_connections
    
    async def test_multiple_connections_per_user(self):
        """Test handling multiple connections for the same user."""
        cm = ConnectionManager()
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        client_id1 = "test-client-1"
        client_id2 = "test-client-2"
        user_id = "test-user-1"
        
        await cm.connect(ws1, client_id1, user_id)
        await cm.connect(ws2, client_id2, user_id)
        
        assert len(cm.user_connections[user_id]) == 2
        assert client_id1 in cm.user_connections[user_id]
        assert client_id2 in cm.user_connections[user_id]
        
        # Disconnect one client
        cm.disconnect(client_id1, user_id)
        
        assert user_id in cm.user_connections
        assert len(cm.user_connections[user_id]) == 1
        assert client_id2 in cm.user_connections[user_id]
    
    async def test_send_personal_message(self):
        """Test sending a message to a specific user."""
        cm = ConnectionManager()
        ws = MockWebSocket()
        client_id = "test-client-1"
        user_id = "test-user-1"
        
        await cm.connect(ws, client_id, user_id)
        
        message = {"type": "test", "data": {"value": 123}}
        await cm.send_personal_message(message, user_id)
        
        ws.send_json.assert_called_once_with(message)
    
    async def test_send_personal_message_no_user(self):
        """Test sending a message to a non-existent user."""
        cm = ConnectionManager()
        message = {"type": "test", "data": {"value": 123}}
        
        # Should not raise an error
        await cm.send_personal_message(message, "non-existent-user")
    
    async def test_send_personal_message_handles_errors(self):
        """Test that send errors are handled gracefully."""
        cm = ConnectionManager()
        ws = MockWebSocket()
        client_id = "test-client-1"
        user_id = "test-user-1"
        
        # Make send_json raise an exception
        ws.send_json.side_effect = Exception("Connection lost")
        
        await cm.connect(ws, client_id, user_id)
        
        message = {"type": "test", "data": {"value": 123}}
        await cm.send_personal_message(message, user_id)
        
        # Client should be disconnected after error
        assert client_id not in cm.active_connections
        assert user_id not in cm.user_connections
    
    async def test_broadcast(self):
        """Test broadcasting a message to all connected clients."""
        cm = ConnectionManager()
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        client_id1 = "test-client-1"
        client_id2 = "test-client-2"
        user_id1 = "test-user-1"
        user_id2 = "test-user-2"
        
        await cm.connect(ws1, client_id1, user_id1)
        await cm.connect(ws2, client_id2, user_id2)
        
        message = {"type": "broadcast", "data": {"value": 456}}
        await cm.broadcast(message)
        
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)
    
    async def test_broadcast_handles_errors(self):
        """Test that broadcast handles send errors gracefully."""
        cm = ConnectionManager()
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        client_id1 = "test-client-1"
        client_id2 = "test-client-2"
        user_id1 = "test-user-1"
        user_id2 = "test-user-2"
        
        # Make ws1 fail
        ws1.send_json.side_effect = Exception("Connection lost")
        
        await cm.connect(ws1, client_id1, user_id1)
        await cm.connect(ws2, client_id2, user_id2)
        
        message = {"type": "broadcast", "data": {"value": 456}}
        await cm.broadcast(message)
        
        # ws1 should be disconnected
        assert client_id1 not in cm.active_connections
        # ws2 should still receive the message
        ws2.send_json.assert_called_once_with(message)


@pytest.mark.asyncio
class TestWebSocketNotifier:
    """Test WebSocketNotifier functionality."""
    
    @pytest.fixture
    def mock_manager(self, monkeypatch):
        """Mock the global manager instance."""
        mock = MagicMock()
        mock.send_personal_message = AsyncMock()
        monkeypatch.setattr("api.websockets.manager", mock)
        return mock
    
    async def test_document_upload_started(self, mock_manager):
        """Test document upload started notification."""
        user_id = "test-user"
        document_id = "test-doc"
        filename = "test.pdf"
        
        await WebSocketNotifier.document_upload_started(user_id, document_id, filename)
        
        mock_manager.send_personal_message.assert_called_once()
        call_args = mock_manager.send_personal_message.call_args[0]
        message = call_args[0]
        target_user = call_args[1]
        
        assert message["type"] == "document.upload.started"
        assert message["data"]["document_id"] == document_id
        assert message["data"]["filename"] == filename
        assert target_user == user_id
    
    async def test_document_upload_completed(self, mock_manager):
        """Test document upload completed notification."""
        user_id = "test-user"
        document_id = "test-doc"
        filename = "test.pdf"
        
        await WebSocketNotifier.document_upload_completed(user_id, document_id, filename)
        
        mock_manager.send_personal_message.assert_called_once()
        call_args = mock_manager.send_personal_message.call_args[0]
        message = call_args[0]
        
        assert message["type"] == "document.upload.completed"
        assert message["data"]["document_id"] == document_id
        assert message["data"]["filename"] == filename
    
    async def test_document_processing_started(self, mock_manager):
        """Test document processing started notification."""
        user_id = "test-user"
        document_id = "test-doc"
        
        await WebSocketNotifier.document_processing_started(user_id, document_id)
        
        mock_manager.send_personal_message.assert_called_once()
        call_args = mock_manager.send_personal_message.call_args[0]
        message = call_args[0]
        
        assert message["type"] == "document.processing.started"
        assert message["data"]["document_id"] == document_id
    
    async def test_document_processing_progress(self, mock_manager):
        """Test document processing progress notification."""
        user_id = "test-user"
        document_id = "test-doc"
        progress = 0.5
        message_text = "Extracting text"
        
        await WebSocketNotifier.document_processing_progress(
            user_id, document_id, progress, message_text
        )
        
        mock_manager.send_personal_message.assert_called_once()
        call_args = mock_manager.send_personal_message.call_args[0]
        message = call_args[0]
        
        assert message["type"] == "document.processing.progress"
        assert message["data"]["document_id"] == document_id
        assert message["data"]["progress"] == progress
        assert message["data"]["message"] == message_text
    
    async def test_document_processing_completed(self, mock_manager):
        """Test document processing completed notification."""
        user_id = "test-user"
        document_id = "test-doc"
        strategies_count = 5
        
        await WebSocketNotifier.document_processing_completed(
            user_id, document_id, strategies_count
        )
        
        mock_manager.send_personal_message.assert_called_once()
        call_args = mock_manager.send_personal_message.call_args[0]
        message = call_args[0]
        
        assert message["type"] == "document.processing.completed"
        assert message["data"]["document_id"] == document_id
        assert message["data"]["strategies_count"] == strategies_count
    
    async def test_document_processing_failed(self, mock_manager):
        """Test document processing failed notification."""
        user_id = "test-user"
        document_id = "test-doc"
        error_msg = "Failed to parse PDF"
        
        await WebSocketNotifier.document_processing_failed(
            user_id, document_id, error_msg
        )
        
        mock_manager.send_personal_message.assert_called_once()
        call_args = mock_manager.send_personal_message.call_args[0]
        message = call_args[0]
        
        assert message["type"] == "document.processing.failed"
        assert message["data"]["document_id"] == document_id
        assert message["data"]["error"] == error_msg
    
    async def test_strategy_extracted(self, mock_manager):
        """Test strategy extracted notification."""
        user_id = "test-user"
        document_id = "test-doc"
        strategy_id = "strat-1"
        strategy_name = "Long/Short Equity"
        
        await WebSocketNotifier.strategy_extracted(
            user_id, document_id, strategy_id, strategy_name
        )
        
        mock_manager.send_personal_message.assert_called_once()
        call_args = mock_manager.send_personal_message.call_args[0]
        message = call_args[0]
        
        assert message["type"] == "strategy.extracted"
        assert message["data"]["document_id"] == document_id
        assert message["data"]["strategy_id"] == strategy_id
        assert message["data"]["strategy_name"] == strategy_name
    
    async def test_all_notifications_have_timestamp(self, mock_manager):
        """Test that all notifications include a timestamp."""
        test_cases = [
            (WebSocketNotifier.document_upload_started, ("user", "doc", "file.pdf")),
            (WebSocketNotifier.document_upload_completed, ("user", "doc", "file.pdf")),
            (WebSocketNotifier.document_processing_started, ("user", "doc")),
            (WebSocketNotifier.document_processing_progress, ("user", "doc", 0.5, "msg")),
            (WebSocketNotifier.document_processing_completed, ("user", "doc", 3)),
            (WebSocketNotifier.document_processing_failed, ("user", "doc", "error")),
            (WebSocketNotifier.strategy_extracted, ("user", "doc", "strat", "name")),
        ]
        
        for func, args in test_cases:
            mock_manager.send_personal_message.reset_mock()
            await func(*args)
            
            call_args = mock_manager.send_personal_message.call_args[0]
            message = call_args[0]
            
            assert "timestamp" in message
            assert isinstance(message["timestamp"], str)
            # Should be ISO format
            assert "T" in message["timestamp"]