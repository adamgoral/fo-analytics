"""Chat models for AI assistant conversations."""

from enum import StrEnum, auto
from typing import List, Optional

from sqlalchemy import ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SQLEnum

from .base import Base, TimestampMixin


class MessageRole(StrEnum):
    """Enum for message roles in chat conversations."""
    USER = auto()
    ASSISTANT = auto()
    SYSTEM = auto()


class ConversationContext(StrEnum):
    """Enum for types of context attached to conversations."""
    DOCUMENT = auto()
    STRATEGY = auto()
    BACKTEST = auto()
    PORTFOLIO = auto()
    GENERAL = auto()


class ChatSession(Base, TimestampMixin):
    """Model for chat sessions with the AI assistant."""
    
    __tablename__ = "chat_sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    context_type: Mapped[ConversationContext] = mapped_column(
        SQLEnum(ConversationContext), 
        nullable=False,
        default=ConversationContext.GENERAL
    )
    context_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    context_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="chat_sessions")
    messages: Mapped[List["ChatMessage"]] = relationship(
        back_populates="session", 
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )
    
    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, title={self.title}, user_id={self.user_id})>"


class ChatMessage(Base, TimestampMixin):
    """Model for individual messages in a chat session."""
    
    __tablename__ = "chat_messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"), nullable=False)
    role: Mapped[MessageRole] = mapped_column(SQLEnum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    message_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    
    # Relationships
    session: Mapped["ChatSession"] = relationship(back_populates="messages")
    
    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, role={self.role}, session_id={self.session_id})>"