"""Pydantic schemas for request/response validation."""

from .auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    MessageResponse
)
from .strategy import (
    StrategyBase,
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyListResponse
)
from .backtest import (
    BacktestBase,
    BacktestCreate,
    BacktestUpdate,
    BacktestResponse,
    BacktestListResponse,
    BacktestResultsUpload
)
from .document import (
    DocumentBase,
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    DocumentProcessRequest
)

__all__ = [
    # Auth schemas
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    "MessageResponse",
    # Strategy schemas
    "StrategyBase",
    "StrategyCreate",
    "StrategyUpdate",
    "StrategyResponse",
    "StrategyListResponse",
    # Backtest schemas
    "BacktestBase",
    "BacktestCreate",
    "BacktestUpdate",
    "BacktestResponse",
    "BacktestListResponse",
    "BacktestResultsUpload",
    # Document schemas
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentProcessRequest",
]