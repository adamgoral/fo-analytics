"""Tests for WebSocket endpoints."""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from websockets.exceptions import WebSocketException

from src.main import app
from src.api.websockets import notifier, ConnectionManager


@pytest.mark.asyncio
class TestWebSockets:
    """Test WebSocket functionality."""
    
    @pytest.fixture
    def websocket_client(self):
        """Create a test client for WebSocket testing."""
        client = TestClient(app)
        return client
    
    async def test_websocket_connect_with_valid_token(self, websocket_client, async_client):
        """Test WebSocket connection with valid JWT token."""
        # Register and login a test user
        user_data = {
            "name": "WS Test User",
            "email": "wstest@example.com",
            "password": "testPassword123!",
            "role": "viewer"
        }
        
        await async_client.post("/api/v1/auth/register", json=user_data)
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        
        # Mock JWT verification
        with patch('src.api.websockets.verify_token') as mock_verify:
            mock_verify.return_value = {"sub": "wstest@example.com", "user_id": "test-user-id"}
            
            # Connect to WebSocket
            with websocket_client.websocket_connect(f"/ws?token={access_token}") as websocket:
                # Should receive welcome message
                data = websocket.receive_json()
                assert data["type"] == "connection"
                assert data["message"] == "Connected to FO Analytics WebSocket"
    
    async def test_websocket_connect_without_token(self, websocket_client):
        """Test WebSocket connection without token."""
        with pytest.raises(WebSocketException):
            with websocket_client.websocket_connect("/ws"):
                pass
    
    async def test_websocket_connect_with_invalid_token(self, websocket_client):
        """Test WebSocket connection with invalid token."""
        with patch('src.api.websockets.verify_token', side_effect=Exception("Invalid token")):
            with pytest.raises(WebSocketException):
                with websocket_client.websocket_connect("/ws?token=invalid-token"):
                    pass
    
    async def test_document_upload_notification(self, websocket_client, async_client):
        """Test document upload completion notification."""
        # Setup user and token
        user_data = {
            "name": "Doc WS User",
            "email": "docws@example.com",
            "password": "testPassword123!",
            "role": "viewer"
        }
        
        await async_client.post("/api/v1/auth/register", json=user_data)
        login_response = await async_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        user_id = "test-user-id"
        
        with patch('src.api.websockets.verify_token') as mock_verify:
            mock_verify.return_value = {"sub": "docws@example.com", "user_id": user_id}
            
            # Connect to WebSocket
            with websocket_client.websocket_connect(f"/ws?token={access_token}") as websocket:
                # Receive welcome message
                websocket.receive_json()
                
                # Simulate document upload notification
                await notifier.document_upload_completed(
                    user_id=user_id,
                    document_id="doc-123",
                    filename="test.pdf"
                )
                
                # Should receive notification
                notification = websocket.receive_json()
                assert notification["type"] == "document_uploaded"
                assert notification["document_id"] == "doc-123"
                assert notification["filename"] == "test.pdf"
    
    async def test_document_processing_status_notification(self):
        """Test document processing status notification."""
        user_id = "test-user-id"
        document_id = "doc-456"
        
        # Mock active connections
        mock_websocket = AsyncMock()
        notifier.active_connections = {user_id: mock_websocket}
        
        # Send processing started notification
        await notifier.document_processing_started(
            user_id=user_id,
            document_id=document_id
        )
        
        # Verify message was sent
        mock_websocket.send_json.assert_called_once()
        sent_data = mock_websocket.send_json.call_args[0][0]
        assert sent_data["type"] == "document_processing_started"
        assert sent_data["document_id"] == document_id
        
        # Reset mock
        mock_websocket.reset_mock()
        
        # Send processing completed notification
        await notifier.document_processing_completed(
            user_id=user_id,
            document_id=document_id,
            success=True,
            strategies_count=3
        )
        
        # Verify message was sent
        mock_websocket.send_json.assert_called_once()
        sent_data = mock_websocket.send_json.call_args[0][0]
        assert sent_data["type"] == "document_processing_completed"
        assert sent_data["document_id"] == document_id
        assert sent_data["success"] is True
        assert sent_data["strategies_count"] == 3
    
    async def test_backtest_status_notification(self):
        """Test backtest status notification."""
        user_id = "test-user-id"
        backtest_id = 123
        
        # Mock active connections
        mock_websocket = AsyncMock()
        notifier.active_connections = {user_id: mock_websocket}
        
        # Send backtest started notification
        await notifier.backtest_started(
            user_id=user_id,
            backtest_id=backtest_id,
            strategy_name="Test Strategy"
        )
        
        # Verify message was sent
        mock_websocket.send_json.assert_called_once()
        sent_data = mock_websocket.send_json.call_args[0][0]
        assert sent_data["type"] == "backtest_started"
        assert sent_data["backtest_id"] == backtest_id
        assert sent_data["strategy_name"] == "Test Strategy"
    
    async def test_websocket_disconnect_removes_connection(self):
        """Test that disconnecting removes the connection from manager."""
        user_id = "test-user-id"
        mock_websocket = AsyncMock()
        
        # Add connection
        notifier.active_connections[user_id] = mock_websocket
        
        # Disconnect
        await notifier.disconnect(user_id)
        
        # Verify connection was removed
        assert user_id not in notifier.active_connections
    
    async def test_broadcast_message(self):
        """Test broadcasting message to all connected users."""
        # Setup multiple connections
        user1_ws = AsyncMock()
        user2_ws = AsyncMock()
        user3_ws = AsyncMock()
        
        notifier.active_connections = {
            "user1": user1_ws,
            "user2": user2_ws,
            "user3": user3_ws
        }
        
        # Broadcast message
        await notifier.broadcast({
            "type": "system_announcement",
            "message": "System maintenance in 5 minutes"
        })
        
        # Verify all users received the message
        for ws in [user1_ws, user2_ws, user3_ws]:
            ws.send_json.assert_called_once_with({
                "type": "system_announcement",
                "message": "System maintenance in 5 minutes"
            })
    
    async def test_send_personal_message_error_handling(self):
        """Test error handling when sending personal message fails."""
        user_id = "test-user-id"
        mock_websocket = AsyncMock()
        mock_websocket.send_json.side_effect = Exception("Connection closed")
        
        notifier.active_connections = {user_id: mock_websocket}
        
        # Should not raise exception
        await notifier.send_personal_message(
            {"type": "test", "data": "test"},
            user_id
        )
        
        # Connection should be removed after error
        assert user_id not in notifier.active_connections