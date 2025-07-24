"""Strategy API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_active_user
from core.database import get_db
from core.dependencies import get_strategy_repository
from models.user import User
from models.strategy import StrategyStatus
from repositories.strategy import StrategyRepository
from schemas.strategy import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyListResponse
)

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.post("/", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    strategy_data: StrategyCreate,
    current_user: User = Depends(get_current_active_user),
    strategy_repo: StrategyRepository = Depends(get_strategy_repository),
):
    """
    Create a new strategy.
    
    Requires authentication.
    """
    # Create strategy with current user as creator
    strategy_dict = strategy_data.model_dump()
    strategy_dict["created_by_id"] = current_user.id
    
    strategy = await strategy_repo.create(**strategy_dict)
    return strategy


@router.get("/", response_model=StrategyListResponse)
async def list_strategies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[StrategyStatus] = None,
    asset_class: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    strategy_repo: StrategyRepository = Depends(get_strategy_repository),
):
    """
    List strategies accessible to the current user.
    
    - **skip**: Number of strategies to skip (for pagination)
    - **limit**: Maximum number of strategies to return
    - **status**: Filter by strategy status
    - **asset_class**: Filter by asset class
    """
    # Get strategies for current user
    strategies = await strategy_repo.get_by_user(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    # Apply filters if provided
    if status:
        strategies = [s for s in strategies if s.status == status]
    if asset_class:
        strategies = [s for s in strategies if s.asset_class == asset_class]
    
    return StrategyListResponse(
        strategies=strategies,
        total=len(strategies),
        skip=skip,
        limit=limit
    )


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_active_user),
    strategy_repo: StrategyRepository = Depends(get_strategy_repository),
):
    """
    Get a specific strategy by ID.
    
    Requires authentication and ownership.
    """
    strategy = await strategy_repo.get(strategy_id)
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Check ownership
    if strategy.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this strategy"
        )
    
    return strategy


@router.patch("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: int,
    strategy_update: StrategyUpdate,
    current_user: User = Depends(get_current_active_user),
    strategy_repo: StrategyRepository = Depends(get_strategy_repository),
):
    """
    Update a strategy.
    
    Requires authentication and ownership.
    """
    # Check if strategy exists and user owns it
    strategy = await strategy_repo.get(strategy_id)
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    if strategy.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this strategy"
        )
    
    # Update strategy
    update_data = strategy_update.model_dump(exclude_unset=True)
    updated_strategy = await strategy_repo.update(strategy_id, **update_data)
    
    return updated_strategy


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_active_user),
    strategy_repo: StrategyRepository = Depends(get_strategy_repository),
):
    """
    Delete a strategy.
    
    Requires authentication and ownership.
    """
    # Check if strategy exists and user owns it
    strategy = await strategy_repo.get(strategy_id)
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    if strategy.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this strategy"
        )
    
    # Delete strategy
    await strategy_repo.delete(strategy_id)


@router.get("/document/{document_id}", response_model=List[StrategyResponse])
async def get_strategies_by_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    strategy_repo: StrategyRepository = Depends(get_strategy_repository),
):
    """
    Get all strategies extracted from a specific document.
    
    Requires authentication and document ownership.
    """
    # Get strategies for the document
    strategies = await strategy_repo.get_by_document(document_id)
    
    # Filter by ownership
    user_strategies = [s for s in strategies if s.created_by_id == current_user.id]
    
    return user_strategies


@router.post("/{strategy_id}/activate", response_model=StrategyResponse)
async def activate_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_active_user),
    strategy_repo: StrategyRepository = Depends(get_strategy_repository),
):
    """
    Activate a strategy.
    
    Requires authentication and ownership.
    """
    # Check ownership
    strategy = await strategy_repo.get(strategy_id)
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    if strategy.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to activate this strategy"
        )
    
    # Update status
    updated_strategy = await strategy_repo.update(
        strategy_id,
        status=StrategyStatus.ACTIVE
    )
    
    return updated_strategy


@router.post("/{strategy_id}/deactivate", response_model=StrategyResponse)
async def deactivate_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_active_user),
    strategy_repo: StrategyRepository = Depends(get_strategy_repository),
):
    """
    Deactivate a strategy.
    
    Requires authentication and ownership.
    """
    # Check ownership
    strategy = await strategy_repo.get(strategy_id)
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    if strategy.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to deactivate this strategy"
        )
    
    # Update status
    updated_strategy = await strategy_repo.update(
        strategy_id,
        status=StrategyStatus.PAUSED
    )
    
    return updated_strategy


@router.put("/{strategy_id}/code", response_model=StrategyResponse)
async def update_strategy_code(
    strategy_id: int,
    code_update: dict,
    current_user: User = Depends(get_current_active_user),
    strategy_repo: StrategyRepository = Depends(get_strategy_repository),
):
    """
    Update the code implementation of a strategy.
    
    Requires authentication and ownership.
    
    Request body:
    - code: The strategy implementation code
    - code_language: Programming language (default: python)
    """
    # Check ownership
    strategy = await strategy_repo.get(strategy_id)
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    if strategy.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this strategy"
        )
    
    # Update code
    updated_strategy = await strategy_repo.update(
        strategy_id,
        code=code_update.get("code"),
        code_language=code_update.get("code_language", "python")
    )
    
    return updated_strategy