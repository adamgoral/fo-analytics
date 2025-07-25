"""API endpoints for chat functionality."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_active_user
from core.database import get_db
from core.config import settings
from models.user import User
from models.chat import MessageRole
from repositories.chat_repository import ChatRepository, ChatMessageRepository
from repositories.document import DocumentRepository
from repositories.strategy import StrategyRepository
from repositories.backtest import BacktestRepository
from schemas.chat import (
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionResponse,
    ChatSessionWithMessages,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatStreamChunk
)
from services.chat_service import ChatService
from services.llm.service import LLMService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    """Get chat service instance."""
    chat_repo = ChatRepository(db)
    message_repo = ChatMessageRepository(db)
    document_repo = DocumentRepository(db)
    strategy_repo = StrategyRepository(db)
    backtest_repo = BacktestRepository(db)
    llm_service = LLMService()
    
    return ChatService(
        chat_repo=chat_repo,
        message_repo=message_repo,
        llm_service=llm_service,
        document_repo=document_repo,
        strategy_repo=strategy_repo,
        backtest_repo=backtest_repo
    )


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Create a new chat session."""
    try:
        session = await chat_service.create_session(
            user_id=current_user.id,
            session_data=session_data
        )
        
        # Convert to response model
        return ChatSessionResponse(
            id=session.id,
            title=session.title,
            user_id=session.user_id,
            context_type=session.context_type,
            context_id=session.context_id,
            context_data=session.context_data,
            is_active=session.is_active,
            created_at=session.created_at,
            updated_at=session.updated_at
        )
    except ValueError as e:
        logger.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating chat session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create chat session: {str(e)}")


@router.get("/sessions")
async def list_chat_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's chat sessions."""
    chat_repo = ChatRepository(db)
    sessions = await chat_repo.get_user_sessions(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        include_inactive=include_inactive
    )
    
    session_list = [
        ChatSessionResponse(
            id=session.id,
            title=session.title,
            user_id=session.user_id,
            context_type=session.context_type,
            context_id=session.context_id,
            context_data=session.context_data,
            is_active=session.is_active,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=getattr(session, 'message_count', 0),
            last_message_at=getattr(session, 'last_message_at', None)
        )
        for session in sessions
    ]
    
    # Return paginated response
    return {
        "items": session_list,
        "total": len(session_list),  # This is not accurate for total count
        "skip": skip,
        "limit": limit
    }


@router.get("/sessions/{session_id}", response_model=ChatSessionWithMessages)
async def get_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a chat session with messages."""
    chat_repo = ChatRepository(db)
    session = await chat_repo.get_session_with_messages(
        session_id=session_id,
        user_id=current_user.id
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    return ChatSessionWithMessages(
        id=session.id,
        title=session.title,
        user_id=session.user_id,
        context_type=session.context_type,
        context_id=session.context_id,
        context_data=session.context_data,
        is_active=session.is_active,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[
            ChatMessageResponse(
                id=msg.id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                tokens_used=msg.tokens_used,
                model_name=msg.model_name,
                metadata=msg.metadata,
                created_at=msg.created_at
            )
            for msg in session.messages
        ]
    )


@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    session_id: int,
    update_data: ChatSessionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a chat session."""
    chat_repo = ChatRepository(db)
    session = await chat_repo.update_session(
        session_id=session_id,
        user_id=current_user.id,
        update_data=update_data
    )
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        user_id=session.user_id,
        context_type=session.context_type,
        context_id=session.context_id,
        context_data=session.context_data,
        is_active=session.is_active,
        created_at=session.created_at,
        updated_at=session.updated_at
    )


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: int,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Send a message and get AI response."""
    try:
        assistant_message = await chat_service.send_message(
            session_id=session_id,
            user_id=current_user.id,
            message_data=message_data,
            stream=False
        )
        
        return ChatMessageResponse(
            id=assistant_message.id,
            session_id=assistant_message.session_id,
            role=assistant_message.role,
            content=assistant_message.content,
            tokens_used=assistant_message.tokens_used,
            model_name=assistant_message.model_name,
            metadata=assistant_message.metadata,
            created_at=assistant_message.created_at
        )
    except ValueError as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process message")


@router.post("/sessions/{session_id}/messages/stream")
async def stream_message(
    session_id: int,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Send a message and stream AI response."""
    async def generate():
        try:
            async for chunk in await chat_service.send_message(
                session_id=session_id,
                user_id=current_user.id,
                message_data=message_data,
                stream=True
            ):
                yield f"data: {chunk.model_dump_json()}\n\n"
        except Exception as e:
            logger.error(f"Error streaming message: {str(e)}")
            yield f"data: {ChatStreamChunk(content='Error processing message', is_final=True).model_dump_json()}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )

