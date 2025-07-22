from typing import List
from sqlalchemy import String, Text, Integer, ForeignKey, Float, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import StrEnum, auto

from .base import Base, TimestampMixin


class StrategyStatus(StrEnum):
    """Status of a trading strategy."""
    DRAFT = auto()
    ACTIVE = auto()
    PAUSED = auto()
    ARCHIVED = auto()


class AssetClass(StrEnum):
    """Asset classes for strategies."""
    EQUITY = auto()
    FIXED_INCOME = auto()
    COMMODITY = auto()
    CURRENCY = auto()
    CRYPTO = auto()
    MULTI_ASSET = auto()


class Strategy(Base, TimestampMixin):
    """Trading strategy extracted from documents."""
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Strategy details
    asset_class: Mapped[AssetClass] = mapped_column(SQLEnum(AssetClass), nullable=False)
    status: Mapped[StrategyStatus] = mapped_column(
        SQLEnum(StrategyStatus), 
        default=StrategyStatus.DRAFT, 
        nullable=False
    )
    
    # Strategy parameters (stored as JSON)
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    entry_rules: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    exit_rules: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    risk_parameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Performance metrics (populated after backtesting)
    expected_return: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_volatility: Mapped[float | None] = mapped_column(Float, nullable=True)
    sharpe_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_drawdown: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # LLM extraction metadata
    extraction_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    extraction_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Foreign keys
    source_document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Relationships
    source_document: Mapped["Document"] = relationship(back_populates="strategies")
    created_by: Mapped["User"] = relationship(back_populates="strategies")
    backtests: Mapped[List["Backtest"]] = relationship(back_populates="strategy", cascade="all, delete-orphan")