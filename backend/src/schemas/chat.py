"""Pydantic schemas for chat functionality."""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

from models.chat import MessageRole, ConversationContext


class ChatSessionCreate(BaseModel):
    """Schema for creating a new chat session."""
    title: str = Field(..., min_length=1, max_length=255, description="Title of the chat session")
    context_type: ConversationContext = Field(
        default=ConversationContext.GENERAL,
        description="Type of context for the conversation"
    )
    context_id: Optional[int] = Field(None, description="ID of the related context object")
    context_data: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional context data for the session"
    )


class ChatSessionUpdate(BaseModel):
    """Schema for updating a chat session."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class ChatMessageCreate(BaseModel):
    """Schema for creating a new chat message."""
    content: str = Field(..., min_length=1, description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional message metadata")


class ChatMessageResponse(BaseModel):
    """Schema for chat message responses."""
    id: int
    session_id: int
    role: MessageRole
    content: str
    tokens_used: Optional[int] = None
    model_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    """Schema for chat session responses."""
    id: int
    title: str
    user_id: int
    context_type: ConversationContext
    context_id: Optional[int] = None
    context_data: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = None
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatSessionWithMessages(ChatSessionResponse):
    """Schema for chat session with messages."""
    messages: List[ChatMessageResponse] = []


class ChatStreamChunk(BaseModel):
    """Schema for streaming chat response chunks."""
    content: str
    is_final: bool = False
    tokens_used: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None