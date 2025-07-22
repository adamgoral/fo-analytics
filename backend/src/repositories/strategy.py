"""Strategy repository with strategy-specific operations."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.strategy import Strategy
from repositories.base import BaseRepository


class StrategyRepository(BaseRepository[Strategy]):
    """Repository for strategy-specific database operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Strategy, session)

    async def get_by_document(
        self, document_id: int
    ) -> List[Strategy]:
        """Get all strategies extracted from a specific document."""
        result = await self.session.execute(
            select(Strategy)
            .where(Strategy.source_document_id == document_id)
        )
        return list(result.scalars().all())

    async def get_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Strategy]:
        """Get all strategies for a specific user."""
        result = await self.session.execute(
            select(Strategy)
            .where(Strategy.created_by_id == user_id)
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
                Strategy.created_by_id == user_id,
                Strategy.status == "active"
            )
        )
        return list(result.scalars().all())

    async def update_extraction_confidence(
        self, strategy_id: int, extraction_confidence: float
    ) -> Optional[Strategy]:
        """Update strategy extraction confidence score."""
        return await self.update(
            strategy_id, 
            extraction_confidence=extraction_confidence
        )