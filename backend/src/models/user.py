from datetime import datetime
from typing import List
from sqlalchemy import String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import StrEnum, auto

from .base import Base, TimestampMixin


class UserRole(StrEnum):
    """User roles for role-based access control."""
    ADMIN = auto()
    ANALYST = auto()
    VIEWER = auto()


class User(Base, TimestampMixin):
    """User model for authentication and authorization."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    documents: Mapped[List["Document"]] = relationship(back_populates="uploaded_by", cascade="all, delete-orphan")
    strategies: Mapped[List["Strategy"]] = relationship(back_populates="created_by", cascade="all, delete-orphan")
    backtests: Mapped[List["Backtest"]] = relationship(back_populates="created_by", cascade="all, delete-orphan")
    chat_sessions: Mapped[List["ChatSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")