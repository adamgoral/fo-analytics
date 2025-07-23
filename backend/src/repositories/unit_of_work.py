"""Unit of Work pattern for managing transactions across repositories."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import async_session_maker
from repositories.backtest import BacktestRepository
from repositories.document import DocumentRepository
from repositories.strategy import StrategyRepository
from repositories.user import UserRepository


class UnitOfWork:
    """Unit of Work pattern implementation for transaction management."""

    def __init__(self):
        self._session: Optional[AsyncSession] = None
        self.users: Optional[UserRepository] = None
        self.documents: Optional[DocumentRepository] = None
        self.strategies: Optional[StrategyRepository] = None
        self.backtests: Optional[BacktestRepository] = None

    async def __aenter__(self):
        """Enter the async context manager."""
        self._session = async_session_maker()
        await self._session.__aenter__()
        self.users = UserRepository(self._session)
        self.documents = DocumentRepository(self._session)
        self.strategies = StrategyRepository(self._session)
        self.backtests = BacktestRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager."""
        if exc_type:
            await self.rollback()
        await self._session.__aexit__(exc_type, exc_val, exc_tb)

    async def commit(self):
        """Commit the transaction."""
        await self._session.commit()

    async def rollback(self):
        """Rollback the transaction."""
        await self._session.rollback()

    async def refresh(self, instance):
        """Refresh an instance from the database."""
        await self._session.refresh(instance)