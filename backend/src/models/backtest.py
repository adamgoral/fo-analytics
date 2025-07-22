from datetime import datetime, date
from sqlalchemy import String, Text, Integer, ForeignKey, Float, Date, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import StrEnum, auto

from .base import Base, TimestampMixin


class BacktestStatus(StrEnum):
    """Status of a backtest run."""
    QUEUED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class BacktestProvider(StrEnum):
    """Backtest provider/engine used."""
    QUANTCONNECT = auto()
    BACKTRADER = auto()
    ZIPLINE = auto()
    VECTORBT = auto()
    CUSTOM = auto()


class Backtest(Base, TimestampMixin):
    """Backtest results for strategies."""
    __tablename__ = "backtests"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Backtest configuration
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    initial_capital: Mapped[float] = mapped_column(Float, nullable=False)
    provider: Mapped[BacktestProvider] = mapped_column(SQLEnum(BacktestProvider), nullable=False)
    
    # Execution details
    status: Mapped[BacktestStatus] = mapped_column(
        SQLEnum(BacktestStatus), 
        default=BacktestStatus.QUEUED, 
        nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Results
    total_return: Mapped[float | None] = mapped_column(Float, nullable=True)
    annualized_return: Mapped[float | None] = mapped_column(Float, nullable=True)
    volatility: Mapped[float | None] = mapped_column(Float, nullable=True)
    sharpe_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    sortino_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_drawdown: Mapped[float | None] = mapped_column(Float, nullable=True)
    win_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Detailed results (stored as JSON)
    equity_curve: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    trades: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    statistics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Configuration used (for reproducibility)
    configuration: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    
    # Foreign keys
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.id"), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Relationships
    strategy: Mapped["Strategy"] = relationship(back_populates="backtests")
    created_by: Mapped["User"] = relationship(back_populates="backtests")