"""Authentication service for user registration and login."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import (
    create_token_pair,
    get_password_hash,
    verify_password,
    verify_token,
    TokenData
)
from ..models.user import User
from ..repositories.user import UserRepository
from ..repositories.uow import UnitOfWork
from ..schemas.auth import UserCreate, UserLogin


class AuthService:
    """Service for handling authentication operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
    
    async def register(self, user_data: UserCreate) -> User:
        """
        Register a new user.
        
        Args:
            user_data: User creation data
            
        Returns:
            The created user
            
        Raises:
            ValueError: If email already exists
        """
        async with UnitOfWork(self.db) as uow:
            existing_user = await self.user_repo.get_by_email(user_data.email)
            if existing_user:
                raise ValueError("Email already registered")
            
            hashed_password = get_password_hash(user_data.password)
            
            user = User(
                name=user_data.name,
                email=user_data.email,
                hashed_password=hashed_password,
                role=user_data.role or "viewer",
                is_active=True
            )
            
            created_user = await self.user_repo.create(user)
            await uow.commit()
            
            return created_user
    
    async def login(self, login_data: UserLogin) -> tuple[User, TokenData]:
        """
        Authenticate a user and return tokens.
        
        Args:
            login_data: Login credentials
            
        Returns:
            Tuple of user and token data
            
        Raises:
            ValueError: If credentials are invalid
        """
        user = await self.user_repo.get_by_email(login_data.email)
        
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise ValueError("Invalid email or password")
        
        if not user.is_active:
            raise ValueError("User account is inactive")
        
        tokens = create_token_pair(str(user.id), user.role)
        
        return user, tokens
    
    async def refresh_token(self, refresh_token: str) -> Optional[TokenData]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            New token pair if valid, None otherwise
        """
        token_payload = verify_token(refresh_token, token_type="refresh")
        
        if not token_payload:
            return None
        
        user = await self.user_repo.get(token_payload.sub)
        
        if not user or not user.is_active:
            return None
        
        return create_token_pair(str(user.id), user.role)
    
    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password.
        
        Args:
            user_id: The user's ID
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if successful, False otherwise
        """
        async with UnitOfWork(self.db) as uow:
            user = await self.user_repo.get(user_id)
            
            if not user or not verify_password(current_password, user.hashed_password):
                return False
            
            user.hashed_password = get_password_hash(new_password)
            await self.user_repo.update(user)
            await uow.commit()
            
            return True