"""User repository with user-specific operations."""

from typing import Optional, Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user-specific database operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get(self, id: Union[int, str]) -> Optional[User]:
        """Get a user by ID (override to handle int IDs)."""
        if isinstance(id, str):
            id = int(id)
        result = await self.session.execute(
            select(User).where(User.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_active_users(
        self, skip: int = 0, limit: int = 100
    ) -> list[User]:
        """Get all active users with pagination."""
        result = await self.session.execute(
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, id: Union[int, str], **kwargs) -> Optional[User]:
        """Update a user (override to handle int IDs)."""
        if isinstance(id, str):
            id = int(id)
        db_obj = await self.get(id)
        if not db_obj:
            return None
        
        for key, value in kwargs.items():
            setattr(db_obj, key, value)
        
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def activate_user(self, user_id: Union[int, str]) -> Optional[User]:
        """Activate a user account."""
        return await self.update(user_id, is_active=True)

    async def deactivate_user(self, user_id: Union[int, str]) -> Optional[User]:
        """Deactivate a user account."""
        return await self.update(user_id, is_active=False)

    async def update_last_login(self, user_id: Union[int, str]) -> Optional[User]:
        """Update user's last login timestamp."""
        from datetime import datetime, timezone
        
        return await self.update(
            user_id, 
            last_login=datetime.now(timezone.utc)
        )