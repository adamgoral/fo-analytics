"""User API endpoints demonstrating repository pattern usage."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from src.core.dependencies import get_user_repository
from src.repositories.user import UserRepository

router = APIRouter(prefix="/users", tags=["users"])


class UserResponse(BaseModel):
    """User response schema."""
    
    id: UUID
    email: EmailStr
    username: str
    full_name: str
    is_active: bool


class UserCreate(BaseModel):
    """User creation schema."""
    
    email: EmailStr
    username: str
    full_name: str
    password: str


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Get a user by ID."""
    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
    )


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """List all users with pagination."""
    users = await user_repo.get_all(skip=skip, limit=limit)
    
    return [
        UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
        )
        for user in users
    ]


@router.get("/active/", response_model=List[UserResponse])
async def list_active_users(
    skip: int = 0,
    limit: int = 100,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """List active users with pagination."""
    users = await user_repo.get_active_users(skip=skip, limit=limit)
    
    return [
        UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
        )
        for user in users
    ]