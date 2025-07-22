"""User service with business logic."""

from typing import Optional
from uuid import UUID

from repositories.unit_of_work import UnitOfWork
from repositories.user import UserRepository


class UserService:
    """Service layer for user-related business logic."""

    def __init__(self, user_repository: UserRepository):
        self.repository = user_repository

    async def get_user_by_id(self, user_id: UUID) -> Optional[dict]:
        """Get user by ID and return as dict."""
        user = await self.repository.get(user_id)
        if not user:
            return None
        
        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
        }

    async def create_user(
        self,
        email: str,
        username: str,
        full_name: str,
        hashed_password: str,
    ) -> dict:
        """Create a new user."""
        # Check if user already exists
        existing_user = await self.repository.get_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        existing_username = await self.repository.get_by_username(username)
        if existing_username:
            raise ValueError("User with this username already exists")
        
        # Create new user
        user = await self.repository.create(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=hashed_password,
        )
        
        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
        }


class UserServiceWithUoW:
    """Example of using Unit of Work pattern for complex transactions."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_user_with_initial_document(
        self,
        email: str,
        username: str,
        full_name: str,
        hashed_password: str,
        document_name: str,
        document_content: str,
    ) -> dict:
        """Create user and their first document in a single transaction."""
        try:
            # Create user
            user = await self.uow.users.create(
                email=email,
                username=username,
                full_name=full_name,
                hashed_password=hashed_password,
            )
            
            # Create initial document
            document = await self.uow.documents.create(
                user_id=user.id,
                name=document_name,
                content=document_content,
                file_type="text",
                status="pending",
            )
            
            # Commit transaction
            await self.uow.commit()
            
            return {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                },
                "document": {
                    "id": str(document.id),
                    "name": document.name,
                    "status": document.status,
                },
            }
        except Exception:
            await self.uow.rollback()
            raise