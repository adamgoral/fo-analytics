"""WebSocket routes for real-time updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from typing import Optional
import uuid

from src.db.database import get_db
from src.db.models import User
from src.core.config import settings
from src.api.websockets import manager
import structlog

logger = structlog.get_logger()

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user_from_token(token: str, db: AsyncSession) -> Optional[User]:
    """Extract user from JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
            
        user = await db.get(User, email)
        return user
    except JWTError:
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time updates."""
    user = await get_current_user_from_token(token, db)
    
    if not user:
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    client_id = str(uuid.uuid4())
    
    await manager.connect(websocket, client_id, user.email)
    
    try:
        await websocket.send_json({
            "type": "connection.established",
            "data": {
                "client_id": client_id,
                "user_id": user.email
            }
        })
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": data.get("timestamp")
                })
            else:
                logger.info(
                    "websocket_message_received",
                    client_id=client_id,
                    user_id=user.email,
                    message_type=data.get("type")
                )
                
    except WebSocketDisconnect:
        manager.disconnect(client_id, user.email)
        logger.info(
            "websocket_client_disconnected",
            client_id=client_id,
            user_id=user.email
        )
    except Exception as e:
        logger.error(
            "websocket_error",
            client_id=client_id,
            user_id=user.email,
            error=str(e)
        )
        manager.disconnect(client_id, user.email)