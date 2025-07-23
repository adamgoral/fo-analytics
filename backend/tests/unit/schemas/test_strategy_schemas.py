"""Tests for strategy-related schemas."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from schemas.strategy import StrategyBase, StrategyCreate, StrategyUpdate, StrategyResponse
from models.strategy import AssetClass, StrategyStatus


class TestStrategySchemas:
    """Test strategy schema validation."""
    
    def test_strategy_create_valid(self):
        """Test creating valid StrategyCreate schema."""
        data = {
            "name": "Test Strategy",
            "description": "A test trading strategy",
            "asset_class": AssetClass.EQUITY.value,
            "parameters": {"param1": "value1"},
            "entry_rules": {"rule": "buy when MA crosses"},
            "exit_rules": {"rule": "sell when profit > 10%"},
            "risk_parameters": {"max_loss": 0.02}
        }
        
        strategy = StrategyCreate(**data)
        assert strategy.name == "Test Strategy"
        assert strategy.description == "A test trading strategy"
        assert strategy.asset_class == AssetClass.EQUITY
        assert strategy.parameters == {"param1": "value1"}
        assert strategy.entry_rules == {"rule": "buy when MA crosses"}
        assert strategy.exit_rules == {"rule": "sell when profit > 10%"}
        assert strategy.risk_parameters == {"max_loss": 0.02}
    
    def test_strategy_create_missing_required_fields(self):
        """Test StrategyCreate with missing required fields."""
        data = {
            "name": "Test Strategy"
            # Missing required fields
        }
        
        with pytest.raises(ValidationError) as exc_info:
            StrategyCreate(**data)
        
        errors = exc_info.value.errors()
        assert len(errors) >= 6  # Missing multiple required fields
    
    def test_strategy_create_invalid_asset_class(self):
        """Test StrategyCreate with invalid asset class."""
        data = {
            "name": "Test Strategy",
            "description": "Test",
            "asset_class": "invalid_class",
            "parameters": {},
            "entry_rules": {},
            "exit_rules": {},
            "risk_parameters": {}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            StrategyCreate(**data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("asset_class",) for error in errors)
    
    def test_strategy_update_partial(self):
        """Test StrategyUpdate with partial data."""
        data = {
            "name": "Updated Strategy Name",
            "status": StrategyStatus.ACTIVE.value
        }
        
        update = StrategyUpdate(**data)
        assert update.name == "Updated Strategy Name"
        assert update.status == StrategyStatus.ACTIVE
        assert update.description is None
        assert update.parameters is None
    
    def test_strategy_update_all_fields(self):
        """Test StrategyUpdate with all fields."""
        data = {
            "name": "Updated Strategy",
            "description": "Updated description",
            "status": StrategyStatus.INACTIVE.value,
            "parameters": {"new_param": "value"},
            "entry_rules": {"new_rule": "entry"},
            "exit_rules": {"new_rule": "exit"},
            "risk_parameters": {"new_risk": "param"}
        }
        
        update = StrategyUpdate(**data)
        assert update.name == "Updated Strategy"
        assert update.description == "Updated description"
        assert update.status == StrategyStatus.INACTIVE
        assert update.parameters == {"new_param": "value"}
        assert update.entry_rules == {"new_rule": "entry"}
        assert update.exit_rules == {"new_rule": "exit"}
        assert update.risk_parameters == {"new_risk": "param"}
    
    def test_strategy_response(self):
        """Test StrategyResponse schema."""
        data = {
            "id": 1,
            "name": "Test Strategy",
            "description": "A test trading strategy",
            "asset_class": AssetClass.EQUITY.value,
            "status": StrategyStatus.ACTIVE.value,
            "parameters": {"param": "value"},
            "entry_rules": {"rule": "entry"},
            "exit_rules": {"rule": "exit"},
            "risk_parameters": {"risk": "low"},
            "extraction_confidence": 0.95,
            "performance_metrics": {"sharpe_ratio": 1.5},
            "source_document_id": 1,
            "created_by_id": 1,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00"
        }
        
        response = StrategyResponse(**data)
        assert response.id == 1
        assert response.name == "Test Strategy"
        assert response.asset_class == AssetClass.EQUITY
        assert response.status == StrategyStatus.ACTIVE
        assert response.extraction_confidence == 0.95
        assert response.performance_metrics == {"sharpe_ratio": 1.5}