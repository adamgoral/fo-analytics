"""Integration tests for WebSocket endpoints."""

import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt
from datetime import datetime, timedelta

from main import app
from core.config import settings
from models.user import User
from repositories.user import UserRepository


@pytest.mark.asyncio
class TestWebSocketEndpoint:
    """Test WebSocket endpoint functionality."""
    
    @pytest.fixture
    async def test_user(self, db_session: AsyncSession):
        """Create a test user."""
        user_repo = UserRepository(db_session)
        user = await user_repo.create(
            email="wstest@example.com",
            hashed_password="hashed_password",
            full_name="WebSocket Test User",
            role="analyst"
        )
        await db_session.commit()
        return user
    
    @pytest.fixture
    def auth_token(self, test_user: User):
        """Generate a valid auth token for the test user."""
        payload = {
            "sub": test_user.email,
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    @pytest.fixture
    def expired_token(self, test_user: User):
        """Generate an expired auth token."""
        payload = {
            "sub": test_user.email,
            "exp": datetime.utcnow() - timedelta(minutes=1)
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    @pytest.fixture
    def invalid_token(self):
        """Generate an invalid auth token."""
        return "invalid.token.here"
    
    def test_websocket_connect_success(self, auth_token: str):
        """Test successful WebSocket connection."""
        client = TestClient(app)
        
        with client.websocket_connect(f"/api/v1/ws?token={auth_token}") as websocket:
            # Should receive connection established message
            data = websocket.receive_json()
            assert data["type"] == "connection.established"
            assert "client_id" in data["data"]
            assert "user_id" in data["data"]
            assert data["data"]["user_id"] == "wstest@example.com"
    
    def test_websocket_connect_no_token(self):
        """Test WebSocket connection without token."""
        client = TestClient(app)
        
        with pytest.raises(Exception) as exc_info:
            with client.websocket_connect("/api/v1/ws") as websocket:
                pass
        
        # Should fail to connect
        assert "422" in str(exc_info.value) or "Unprocessable Entity" in str(exc_info.value)
    
    def test_websocket_connect_invalid_token(self, invalid_token: str):
        """Test WebSocket connection with invalid token."""
        client = TestClient(app)
        
        with pytest.raises(Exception) as exc_info:
            with client.websocket_connect(f"/api/v1/ws?token={invalid_token}") as websocket:
                # Should close connection
                pass
        
        # Connection should be refused
        assert exc_info.value is not None
    
    def test_websocket_connect_expired_token(self, expired_token: str):
        """Test WebSocket connection with expired token."""
        client = TestClient(app)
        
        with pytest.raises(Exception) as exc_info:
            with client.websocket_connect(f"/api/v1/ws?token={expired_token}") as websocket:
                pass
        
        # Connection should be refused
        assert exc_info.value is not None
    
    def test_websocket_ping_pong(self, auth_token: str):
        """Test WebSocket ping/pong mechanism."""
        client = TestClient(app)
        
        with client.websocket_connect(f"/api/v1/ws?token={auth_token}") as websocket:
            # Receive connection message
            websocket.receive_json()
            
            # Send ping
            ping_message = {
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            }
            websocket.send_json(ping_message)
            
            # Should receive pong
            pong = websocket.receive_json()
            assert pong["type"] == "pong"
            assert pong["timestamp"] == ping_message["timestamp"]
    
    def test_websocket_handles_unknown_message(self, auth_token: str):
        """Test WebSocket handles unknown message types."""
        client = TestClient(app)
        
        with client.websocket_connect(f"/api/v1/ws?token={auth_token}") as websocket:
            # Receive connection message
            websocket.receive_json()
            
            # Send unknown message type
            websocket.send_json({
                "type": "unknown_type",
                "data": {"test": "value"}
            })
            
            # Connection should remain open, can still ping
            websocket.send_json({"type": "ping", "timestamp": "2025-07-23T10:00:00"})
            pong = websocket.receive_json()
            assert pong["type"] == "pong"
    
    @pytest.mark.parametrize("message_type,expected_log", [
        ("document.start", "document.start"),
        ("test.message", "test.message"),
        ("custom_event", "custom_event"),
    ])
    def test_websocket_logs_message_types(
        self, auth_token: str, message_type: str, expected_log: str
    ):
        """Test that WebSocket logs different message types."""
        client = TestClient(app)
        
        with client.websocket_connect(f"/api/v1/ws?token={auth_token}") as websocket:
            # Receive connection message
            websocket.receive_json()
            
            # Send message
            websocket.send_json({
                "type": message_type,
                "data": {"value": 123}
            })
            
            # Verify connection still works
            websocket.send_json({"type": "ping", "timestamp": "2025-07-23T10:00:00"})
            pong = websocket.receive_json()
            assert pong["type"] == "pong"


@pytest.mark.asyncio
class TestWebSocketNotifications:
    """Test WebSocket notifications in API endpoints."""
    
    @pytest.fixture
    async def authenticated_client(self, client: TestClient, test_user: User):
        """Get an authenticated test client."""
        # Login to get token
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": "password123"}
        )
        token = response.json()["access_token"]
        
        # Set authorization header
        client.headers["Authorization"] = f"Bearer {token}"
        return client
    
    async def test_document_upload_sends_notifications(
        self, authenticated_client: TestClient, monkeypatch
    ):
        """Test that document upload sends WebSocket notifications."""
        from api.websockets import notifier
        
        # Mock the notifier methods
        notifier.document_upload_started = AsyncMock()
        notifier.document_upload_completed = AsyncMock()
        
        # Upload a document
        files = {"file": ("test.pdf", b"PDF content", "application/pdf")}
        response = authenticated_client.post(
            "/api/v1/documents/upload",
            files=files,
            data={"document_type": "research_report"}
        )
        
        assert response.status_code == 201
        
        # Verify notifications were sent
        notifier.document_upload_started.assert_called_once()
        notifier.document_upload_completed.assert_called_once()
        
        # Check notification parameters
        upload_completed_call = notifier.document_upload_completed.call_args[1]
        assert "user_id" in upload_completed_call
        assert "document_id" in upload_completed_call
        assert upload_completed_call["filename"] == "test.pdf"