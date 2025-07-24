"""Backtest API endpoints."""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from core.auth import get_current_active_user
from core.database import get_db
from core.dependencies import get_backtest_repository, get_strategy_repository
from models.user import User
from models.backtest import BacktestStatus
from repositories.backtest import BacktestRepository
from repositories.strategy import StrategyRepository
# from repositories.unit_of_work import UnitOfWork  # TODO: Implement UnitOfWork
from schemas.backtest import (
    BacktestCreate,
    BacktestUpdate,
    BacktestResponse,
    BacktestListResponse,
    BacktestResultsUpload
)
from services.backtesting import BacktestingService
from messaging.publisher import MessagePublisher

router = APIRouter(prefix="/backtests", tags=["backtests"])
logger = structlog.get_logger(__name__)


@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_backtest(
    backtest_data: BacktestCreate,
    current_user: User = Depends(get_current_active_user),
    # uow: UnitOfWork = Depends(get_unit_of_work),  # TODO: Implement UnitOfWork
):
    """
    Create a new backtest for a strategy and run it asynchronously.
    
    Requires authentication and strategy ownership.
    The backtest will be queued and executed in the background.
    """
    # Create backtesting service
    backtest_service = BacktestingService(uow)
    
    # Verify strategy ownership
    async with uow:
        strategy = await uow.strategies.get(backtest_data.strategy_id)
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy not found"
            )
        
        if strategy.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create backtests for this strategy"
            )
    
    # Create and run backtest
    result = await backtest_service.create_and_run_backtest(
        backtest_data,
        current_user.id
    )
    
    return result


@router.get("/", response_model=BacktestListResponse)
async def list_backtests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[BacktestStatus] = None,
    strategy_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    backtest_repo: BacktestRepository = Depends(get_backtest_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    List backtests accessible to the current user.
    
    - **skip**: Number of backtests to skip (for pagination)
    - **limit**: Maximum number of backtests to return
    - **status**: Filter by backtest status
    - **strategy_id**: Filter by strategy ID
    """
    # Base query for user's backtests
    from sqlalchemy import select, func
    from models.backtest import Backtest
    
    query = select(Backtest).where(Backtest.created_by_id == current_user.id)
    count_query = select(func.count(Backtest.id)).where(Backtest.created_by_id == current_user.id)
    
    if status:
        query = query.where(Backtest.status == status)
        count_query = count_query.where(Backtest.status == status)
        
    if strategy_id:
        query = query.where(Backtest.strategy_id == strategy_id)
        count_query = count_query.where(Backtest.strategy_id == strategy_id)
        
    query = query.order_by(Backtest.created_at.desc()).offset(skip).limit(limit)
    
    # Execute queries
    result = await db.execute(query)
    backtests = result.scalars().all()
    
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    return BacktestListResponse(
        backtests=[BacktestResponse.model_validate(b) for b in backtests],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{backtest_id}", response_model=BacktestResponse)
async def get_backtest(
    backtest_id: int,
    current_user: User = Depends(get_current_active_user),
    backtest_repo: BacktestRepository = Depends(get_backtest_repository),
):
    """
    Get a specific backtest by ID.
    
    Requires authentication and ownership.
    """
    backtest = await backtest_repo.get(backtest_id)
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found"
        )
    
    # Check ownership
    if backtest.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this backtest"
        )
    
    return backtest


@router.patch("/{backtest_id}", response_model=BacktestResponse)
async def update_backtest(
    backtest_id: int,
    backtest_update: BacktestUpdate,
    current_user: User = Depends(get_current_active_user),
    backtest_repo: BacktestRepository = Depends(get_backtest_repository),
):
    """
    Update a backtest.
    
    Requires authentication and ownership.
    """
    # Check if backtest exists and user owns it
    backtest = await backtest_repo.get(backtest_id)
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found"
        )
    
    if backtest.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this backtest"
        )
    
    # Update backtest
    update_data = backtest_update.model_dump(exclude_unset=True)
    updated_backtest = await backtest_repo.update(backtest_id, **update_data)
    
    return updated_backtest


@router.delete("/{backtest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backtest(
    backtest_id: int,
    current_user: User = Depends(get_current_active_user),
    backtest_repo: BacktestRepository = Depends(get_backtest_repository),
):
    """
    Delete a backtest.
    
    Requires authentication and ownership.
    """
    # Check if backtest exists and user owns it
    backtest = await backtest_repo.get(backtest_id)
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found"
        )
    
    if backtest.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this backtest"
        )
    
    # Delete backtest
    await backtest_repo.delete(backtest_id)


@router.get("/strategy/{strategy_id}", response_model=List[BacktestResponse])
async def get_backtests_by_strategy(
    strategy_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    backtest_repo: BacktestRepository = Depends(get_backtest_repository),
    strategy_repo: StrategyRepository = Depends(get_strategy_repository),
):
    """
    Get all backtests for a specific strategy.
    
    Requires authentication and strategy ownership.
    """
    # Verify strategy ownership
    strategy = await strategy_repo.get(strategy_id)
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    if strategy.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view backtests for this strategy"
        )
    
    # Get backtests for the strategy
    backtests = await backtest_repo.get_by_strategy(
        strategy_id=strategy_id,
        skip=skip,
        limit=limit
    )
    
    return backtests


@router.post("/{backtest_id}/start", response_model=BacktestResponse)
async def start_backtest(
    backtest_id: int,
    current_user: User = Depends(get_current_active_user),
    backtest_repo: BacktestRepository = Depends(get_backtest_repository),
    strategy_repo: StrategyRepository = Depends(get_strategy_repository),
):
    """
    Start a queued backtest.
    
    Requires authentication and ownership.
    """
    # Check ownership and status
    backtest = await backtest_repo.get(backtest_id)
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found"
        )
    
    if backtest.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to start this backtest"
        )
    
    if backtest.status != BacktestStatus.QUEUED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start backtest in {backtest.status} status"
        )
    
    # Update status to running
    updated_backtest = await backtest_repo.update(
        backtest_id,
        status=BacktestStatus.RUNNING,
        started_at=datetime.utcnow()
    )
    
    # Get the strategy details
    strategy = await strategy_repo.get(backtest.strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Publish backtest execution message to RabbitMQ
    try:
        publisher = MessagePublisher()
        message_id = await publisher.publish_backtest_execution(
            backtest_id=backtest_id,
            user_id=current_user.id,
            strategy_id=strategy.id,
            strategy_name=strategy.name,
            strategy_code=strategy.code,
            parameters=backtest.parameters
        )
        
        logger.info(
            "Published backtest execution message",
            backtest_id=backtest_id,
            message_id=str(message_id),
            strategy_id=strategy.id
        )
    except Exception as e:
        # Log error but don't fail - the backtest is already marked as running
        logger.error(
            "Failed to publish backtest execution message",
            backtest_id=backtest_id,
            strategy_id=strategy.id,
            error=str(e),
            exc_info=True
        )
        # Optionally, revert status back to QUEUED
        await backtest_repo.update(
            backtest_id,
            status=BacktestStatus.QUEUED,
            started_at=None
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start backtest execution"
        )
    
    return updated_backtest


@router.post("/{backtest_id}/cancel", response_model=BacktestResponse)
async def cancel_backtest(
    backtest_id: int,
    current_user: User = Depends(get_current_active_user),
    backtest_repo: BacktestRepository = Depends(get_backtest_repository),
):
    """
    Cancel a running or queued backtest.
    
    Requires authentication and ownership.
    """
    # Check ownership and status
    backtest = await backtest_repo.get(backtest_id)
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found"
        )
    
    if backtest.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this backtest"
        )
    
    if backtest.status not in [BacktestStatus.QUEUED, BacktestStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel backtest in {backtest.status} status"
        )
    
    # Update status to cancelled
    updated_backtest = await backtest_repo.update(
        backtest_id,
        status=BacktestStatus.CANCELLED,
        completed_at=datetime.utcnow()
    )
    
    return updated_backtest


@router.post("/{backtest_id}/results", response_model=BacktestResponse)
async def upload_backtest_results(
    backtest_id: int,
    results: BacktestResultsUpload,
    current_user: User = Depends(get_current_active_user),
    backtest_repo: BacktestRepository = Depends(get_backtest_repository),
):
    """
    Upload results for a completed backtest.
    
    This endpoint is typically used by backtest workers to report results.
    Requires authentication and ownership.
    """
    # Check ownership and status
    backtest = await backtest_repo.get(backtest_id)
    
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found"
        )
    
    if backtest.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this backtest"
        )
    
    if backtest.status != BacktestStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot upload results for backtest in {backtest.status} status"
        )
    
    # Update backtest with results
    update_data = results.model_dump()
    update_data["status"] = BacktestStatus.COMPLETED
    update_data["completed_at"] = datetime.utcnow()
    
    updated_backtest = await backtest_repo.update(backtest_id, **update_data)
    
    return updated_backtest


@router.get("/strategy-types", response_model=List[str])
async def get_available_strategy_types(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get list of available strategy types for backtesting.
    
    Returns the built-in strategy types that can be used for backtesting.
    """
    from services.backtesting import StrategyFactory
    
    factory = StrategyFactory()
    return factory.list_available_strategies()
