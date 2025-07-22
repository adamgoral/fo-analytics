"""Dependency injection for repositories and database sessions."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from repositories.backtest import BacktestRepository
from repositories.document import DocumentRepository
from repositories.strategy import StrategyRepository
from repositories.user import UserRepository


async def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> UserRepository:
    """Get user repository instance."""
    return UserRepository(db)


async def get_document_repository(
    db: AsyncSession = Depends(get_db),
) -> DocumentRepository:
    """Get document repository instance."""
    return DocumentRepository(db)


async def get_strategy_repository(
    db: AsyncSession = Depends(get_db),
) -> StrategyRepository:
    """Get strategy repository instance."""
    return StrategyRepository(db)


async def get_backtest_repository(
    db: AsyncSession = Depends(get_db),
) -> BacktestRepository:
    """Get backtest repository instance."""
    return BacktestRepository(db)