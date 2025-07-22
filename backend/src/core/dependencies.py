"""Dependency injection for repositories and database sessions."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.backtest import BacktestRepository
from src.repositories.document import DocumentRepository
from src.repositories.strategy import StrategyRepository
from src.repositories.user import UserRepository


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