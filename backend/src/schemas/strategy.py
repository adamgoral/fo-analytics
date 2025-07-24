"""Strategy-related schemas for API endpoints."""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from models.strategy import StrategyStatus, AssetClass


class StrategyBase(BaseModel):
    """Base strategy schema."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    asset_class: AssetClass
    parameters: Dict = Field(default_factory=dict)
    entry_rules: Dict = Field(default_factory=dict)
    exit_rules: Dict = Field(default_factory=dict)
    risk_parameters: Dict = Field(default_factory=dict)
    code: Optional[str] = None
    code_language: str = Field(default="python")


class StrategyCreate(StrategyBase):
    """Schema for creating a strategy."""
    
    source_document_id: int


class StrategyUpdate(BaseModel):
    """Schema for updating a strategy."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    asset_class: Optional[AssetClass] = None
    status: Optional[StrategyStatus] = None
    parameters: Optional[Dict] = None
    entry_rules: Optional[Dict] = None
    exit_rules: Optional[Dict] = None
    risk_parameters: Optional[Dict] = None
    code: Optional[str] = None
    code_language: Optional[str] = None


class StrategyResponse(BaseModel):
    """Strategy response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: str
    asset_class: AssetClass
    status: StrategyStatus
    parameters: Dict
    entry_rules: Dict
    exit_rules: Dict
    risk_parameters: Dict
    code: Optional[str]
    code_language: str
    
    # Performance metrics
    expected_return: Optional[float]
    expected_volatility: Optional[float]
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    
    # Metadata
    extraction_confidence: float
    extraction_metadata: Optional[Dict]
    source_document_id: int
    created_by_id: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime


class StrategyListResponse(BaseModel):
    """Response for strategy list endpoints."""
    
    strategies: List[StrategyResponse]
    total: int
    skip: int
    limit: int