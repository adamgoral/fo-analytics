"""Strategy repository with strategy-specific operations."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.strategy import Strategy
from src.repositories.base import BaseRepository


class StrategyRepository(BaseRepository[Strategy]):
    """Repository for strategy-specific database operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Strategy, session)

    async def get_by_document(
        self, document_id: UUID
    ) -> List[Strategy]:
        """Get all strategies extracted from a specific document."""
        result = await self.session.execute(
            select(Strategy)
            .where(Strategy.document_id == document_id)
        )
        return list(result.scalars().all())

    async def get_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Strategy]:
        """Get all strategies for a specific user."""
        result = await self.session.execute(
            select(Strategy)
            .where(Strategy.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_strategies(
        self, user_id: UUID
    ) -> List[Strategy]:
        """Get all active strategies for a user."""
        result = await self.session.execute(
            select(Strategy)
            .where(
                Strategy.user_id == user_id,
                Strategy.is_active == True
            )
        )
        return list(result.scalars().all())

    async def activate_strategy(
        self, strategy_id: UUID
    ) -> Optional[Strategy]:
        """Activate a strategy."""
        return await self.update(strategy_id, is_active=True)

    async def deactivate_strategy(
        self, strategy_id: UUID
    ) -> Optional[Strategy]:
        """Deactivate a strategy."""
        return await self.update(strategy_id, is_active=False)

    async def update_confidence_score(
        self, strategy_id: UUID, confidence_score: float
    ) -> Optional[Strategy]:
        """Update strategy confidence score."""
        return await self.update(
            strategy_id, 
            confidence_score=confidence_score
        )