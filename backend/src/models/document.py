from datetime import datetime
from typing import List
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import StrEnum, auto

from .base import Base, TimestampMixin


class DocumentType(StrEnum):
    """Types of documents that can be uploaded."""
    RESEARCH_REPORT = auto()
    STRATEGY_DOCUMENT = auto()
    MARKET_ANALYSIS = auto()
    TRADE_IDEA = auto()
    OTHER = auto()


class DocumentStatus(StrEnum):
    """Processing status of documents."""
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()


class Document(Base, TimestampMixin):
    """Document model for storing uploaded files and their metadata."""
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(SQLEnum(DocumentType), nullable=False)
    
    # Storage information
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # in bytes
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Processing status
    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus), 
        default=DocumentStatus.PENDING, 
        nullable=False
    )
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Extracted metadata (stored as JSON)
    extracted_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Extracted text content
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Foreign keys
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Relationships
    uploaded_by: Mapped["User"] = relationship(back_populates="documents")
    strategies: Mapped[List["Strategy"]] = relationship(back_populates="source_document", cascade="all, delete-orphan")