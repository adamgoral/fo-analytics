"""Base repository with common CRUD operations."""

from typing import Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common database operations."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: Union[int, str]) -> Optional[ModelType]:
        """Get a single record by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get all records with pagination."""
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**kwargs)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, id: Union[int, str], **kwargs) -> Optional[ModelType]:
        """Update an existing record."""
        db_obj = await self.get(id)
        if not db_obj:
            return None
        
        for key, value in kwargs.items():
            setattr(db_obj, key, value)
        
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, id: Union[int, str]) -> bool:
        """Delete a record by ID."""
        db_obj = await self.get(id)
        if not db_obj:
            return False
        
        await self.session.delete(db_obj)
        await self.session.commit()
        return True

    async def exists(self, id: Union[int, str]) -> bool:
        """Check if a record exists by ID."""
        result = await self.session.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None