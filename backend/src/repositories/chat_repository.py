"""Repository for chat-related database operations."""

from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.chat import ChatSession, ChatMessage, MessageRole, ConversationContext
from models.user import User
from schemas.chat import ChatSessionCreate, ChatSessionUpdate, ChatMessageCreate
from repositories.base import BaseRepository


class ChatRepository(BaseRepository[ChatSession]):
    """Repository for chat session operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(ChatSession, db)
    
    async def create_session(
        self, 
        user_id: int, 
        session_data: ChatSessionCreate
    ) -> ChatSession:
        """Create a new chat session."""
        db_session = ChatSession(
            user_id=user_id,
            title=session_data.title,
            context_type=session_data.context_type,
            context_id=session_data.context_id,
            context_data=session_data.context_data
        )
        self.db.add(db_session)
        await self.db.commit()
        await self.db.refresh(db_session)
        return db_session
    
    async def get_user_sessions(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 20,
        include_inactive: bool = False
    ) -> List[ChatSession]:
        """Get all chat sessions for a user."""
        query = select(ChatSession).where(ChatSession.user_id == user_id)
        
        if not include_inactive:
            query = query.where(ChatSession.is_active == True)
        
        # Add message count and last message date
        query = query.outerjoin(ChatMessage).group_by(ChatSession.id)
        query = query.add_columns(
            func.count(ChatMessage.id).label("message_count"),
            func.max(ChatMessage.created_at).label("last_message_at")
        )
        
        query = query.order_by(desc(ChatSession.updated_at))
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        sessions = []
        for row in result:
            session = row[0]
            session.message_count = row[1]
            session.last_message_at = row[2]
            sessions.append(session)
        
        return sessions
    
    async def get_session_with_messages(
        self, 
        session_id: int, 
        user_id: int
    ) -> Optional[ChatSession]:
        """Get a chat session with all its messages."""
        query = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(
                and_(
                    ChatSession.id == session_id,
                    ChatSession.user_id == user_id
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_session(
        self, 
        session_id: int, 
        user_id: int, 
        update_data: ChatSessionUpdate
    ) -> Optional[ChatSession]:
        """Update a chat session."""
        session = await self.get_by_id_and_user(session_id, user_id)
        if not session:
            return None
        
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(session, field, value)
        
        session.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(session)
        return session
    
    async def get_by_id_and_user(
        self, 
        session_id: int, 
        user_id: int
    ) -> Optional[ChatSession]:
        """Get a session by ID ensuring it belongs to the user."""
        query = select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


class ChatMessageRepository(BaseRepository[ChatMessage]):
    """Repository for chat message operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(ChatMessage, db)
    
    async def create_message(
        self,
        session_id: int,
        role: MessageRole,
        content: str,
        tokens_used: Optional[int] = None,
        model_name: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> ChatMessage:
        """Create a new chat message."""
        db_message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            tokens_used=tokens_used,
            model_name=model_name,
            metadata=metadata
        )
        self.db.add(db_message)
        
        # Update session's updated_at timestamp
        session_query = select(ChatSession).where(ChatSession.id == session_id)
        result = await self.db.execute(session_query)
        session = result.scalar_one()
        session.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(db_message)
        return db_message
    
    async def get_session_messages(
        self, 
        session_id: int,
        limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """Get messages for a session."""
        query = select(ChatMessage).where(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at)
        
        if limit:
            query = query.limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_recent_messages(
        self, 
        session_id: int, 
        limit: int = 10
    ) -> List[ChatMessage]:
        """Get the most recent messages for a session."""
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(desc(ChatMessage.created_at))
            .limit(limit)
        )
        result = await self.db.execute(query)
        messages = list(result.scalars().all())
        # Reverse to get chronological order
        return messages[::-1]