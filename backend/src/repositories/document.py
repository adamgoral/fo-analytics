"""Document repository with document-specific operations."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.document import Document
from repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for document-specific database operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Document, session)

    async def get_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """Get all documents for a specific user."""
        result = await self.session.execute(
            select(Document)
            .where(Document.uploaded_by_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_status(
        self, status: str, user_id: Optional[UUID] = None, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """Get documents by processing status."""
        query = select(Document).where(Document.status == status)
        
        if user_id:
            query = query.where(Document.uploaded_by_id == user_id)
            
        result = await self.session.execute(
            query.offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_pending_documents(
        self, limit: int = 10
    ) -> List[Document]:
        """Get documents pending processing."""
        result = await self.session.execute(
            select(Document)
            .where(Document.status == "pending")
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self, document_id: int, status: str
    ) -> Optional[Document]:
        """Update document processing status."""
        return await self.update(document_id, status=status)

    async def mark_as_processed(
        self, document_id: int
    ) -> Optional[Document]:
        """Mark document as processed."""
        return await self.update_status(document_id, "completed")