"""Backtest repository with backtest-specific operations."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.backtest import Backtest
from repositories.base import BaseRepository


class BacktestRepository(BaseRepository[Backtest]):
    """Repository for backtest-specific database operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Backtest, session)

    async def get_by_strategy(
        self, strategy_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Backtest]:
        """Get all backtests for a specific strategy."""
        result = await self.session.execute(
            select(Backtest)
            .where(Backtest.strategy_id == strategy_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_status(
        self, status: str, limit: int = 10
    ) -> List[Backtest]:
        """Get backtests by status."""
        result = await self.session.execute(
            select(Backtest)
            .where(Backtest.status == status)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_pending_backtests(
        self, limit: int = 10
    ) -> List[Backtest]:
        """Get backtests pending execution."""
        return await self.get_by_status("pending", limit)

    async def get_running_backtests(
        self, limit: int = 10
    ) -> List[Backtest]:
        """Get currently running backtests."""
        return await self.get_by_status("running", limit)

    async def update_status(
        self, backtest_id: UUID, status: str
    ) -> Optional[Backtest]:
        """Update backtest status."""
        return await self.update(backtest_id, status=status)

    async def mark_as_completed(
        self, backtest_id: UUID, metrics: dict
    ) -> Optional[Backtest]:
        """Mark backtest as completed with metrics."""
        return await self.update(
            backtest_id,
            status="completed",
            metrics=metrics
        )

    async def mark_as_failed(
        self, backtest_id: UUID, error: str
    ) -> Optional[Backtest]:
        """Mark backtest as failed with error message."""
        return await self.update(
            backtest_id,
            status="failed",
            metrics={"error": error}
        )