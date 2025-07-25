"""WebSocket connection manager and endpoints."""

from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import structlog

logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str, user_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(client_id)
        
        logger.info(
            "websocket_connected",
            client_id=client_id,
            user_id=user_id,
            total_connections=len(self.active_connections)
        )
    
    def disconnect(self, client_id: str, user_id: str):
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(client_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info(
            "websocket_disconnected",
            client_id=client_id,
            user_id=user_id,
            total_connections=len(self.active_connections)
        )
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to all connections for a specific user."""
        if user_id not in self.user_connections:
            return
        
        disconnected_clients = []
        
        for client_id in self.user_connections[user_id]:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_json(message)
                except Exception as e:
                    logger.error(
                        "websocket_send_error",
                        client_id=client_id,
                        error=str(e)
                    )
                    disconnected_clients.append(client_id)
        
        for client_id in disconnected_clients:
            self.disconnect(client_id, user_id)
    
    async def broadcast(self, message: dict):
        """Send a message to all connected clients."""
        disconnected_clients = []
        
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(
                    "websocket_broadcast_error",
                    client_id=client_id,
                    error=str(e)
                )
                disconnected_clients.append(client_id)
        
        for client_id in disconnected_clients:
            for user_id, connections in self.user_connections.items():
                if client_id in connections:
                    self.disconnect(client_id, user_id)
                    break


manager = ConnectionManager()


class WebSocketNotifier:
    """Helper class for sending typed notifications."""
    
    @staticmethod
    async def document_upload_started(user_id: str, document_id: str, filename: str):
        """Notify when document upload starts."""
        await manager.send_personal_message({
            "type": "document.upload.started",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "document_id": document_id,
                "filename": filename
            }
        }, user_id)
    
    @staticmethod
    async def document_upload_completed(user_id: str, document_id: str, filename: str):
        """Notify when document upload completes."""
        await manager.send_personal_message({
            "type": "document.upload.completed",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "document_id": document_id,
                "filename": filename
            }
        }, user_id)
    
    @staticmethod
    async def document_processing_started(user_id: str, document_id: str):
        """Notify when document processing starts."""
        await manager.send_personal_message({
            "type": "document.processing.started",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "document_id": document_id
            }
        }, user_id)
    
    @staticmethod
    async def document_processing_progress(user_id: str, document_id: str, progress: float, message: str):
        """Notify document processing progress."""
        await manager.send_personal_message({
            "type": "document.processing.progress",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "document_id": document_id,
                "progress": progress,
                "message": message
            }
        }, user_id)
    
    @staticmethod
    async def document_processing_completed(user_id: str, document_id: str, strategies_count: int):
        """Notify when document processing completes."""
        await manager.send_personal_message({
            "type": "document.processing.completed",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "document_id": document_id,
                "strategies_count": strategies_count
            }
        }, user_id)
    
    @staticmethod
    async def document_processing_failed(user_id: str, document_id: str, error: str):
        """Notify when document processing fails."""
        await manager.send_personal_message({
            "type": "document.processing.failed",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "document_id": document_id,
                "error": error
            }
        }, user_id)
    
    @staticmethod
    async def strategy_extracted(user_id: str, document_id: str, strategy_id: str, strategy_name: str):
        """Notify when a strategy is extracted."""
        await manager.send_personal_message({
            "type": "strategy.extracted",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "document_id": document_id,
                "strategy_id": strategy_id,
                "strategy_name": strategy_name
            }
        }, user_id)
    
    @staticmethod
    async def send_backtest_notification(
        backtest_id: int,
        status: str,
        message: str,
        progress: int = 0,
        results: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ):
        """Send backtest-related notifications."""
        notification = {
            "type": f"backtest.{status}",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "backtest_id": backtest_id,
                "status": status,
                "message": message,
                "progress": progress
            }
        }
        
        if results:
            notification["data"]["results"] = results
        
        if user_id:
            await manager.send_personal_message(notification, user_id)
        else:
            # For worker processes that don't have user_id, broadcast to all
            # In production, we'd look up the user_id from the backtest
            await manager.broadcast(notification)


# Global instances
manager = ConnectionManager()
notifier = WebSocketNotifier()