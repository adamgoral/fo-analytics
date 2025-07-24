"""Tests for strategy code API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.strategy import Strategy, StrategyStatus, AssetClass
from models.user import User
from models.document import Document, DocumentStatus


@pytest.mark.asyncio
async def test_update_strategy_code(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    auth_headers: dict,
):
    """Test updating strategy code."""
    # Create a test document
    document = Document(
        filename="test.pdf",
        file_path="/path/to/test.pdf",
        file_size=1024,
        mime_type="application/pdf",
        status=DocumentStatus.PROCESSED,
        uploaded_by_id=test_user.id,
    )
    db_session.add(document)
    await db_session.flush()

    # Create a test strategy
    strategy = Strategy(
        name="Test Strategy",
        description="Test description",
        asset_class=AssetClass.EQUITY,
        status=StrategyStatus.DRAFT,
        source_document_id=document.id,
        created_by_id=test_user.id,
        extraction_confidence=0.9,
    )
    db_session.add(strategy)
    await db_session.commit()

    # Update the strategy code
    code_data = {
        "code": """
def calculate_signals(data):
    # Simple moving average crossover
    sma_short = data['close'].rolling(20).mean()
    sma_long = data['close'].rolling(50).mean()
    return (sma_short > sma_long).astype(int)
""",
        "code_language": "python"
    }
    
    response = await client.put(
        f"/api/v1/strategies/{strategy.id}/code",
        json=code_data,
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == code_data["code"]
    assert data["code_language"] == "python"


@pytest.mark.asyncio
async def test_update_strategy_code_unauthorized(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
):
    """Test updating strategy code without authentication."""
    # Create a test document
    document = Document(
        filename="test.pdf",
        file_path="/path/to/test.pdf",
        file_size=1024,
        mime_type="application/pdf",
        status=DocumentStatus.PROCESSED,
        uploaded_by_id=test_user.id,
    )
    db_session.add(document)
    await db_session.flush()

    # Create a test strategy
    strategy = Strategy(
        name="Test Strategy",
        description="Test description",
        asset_class=AssetClass.EQUITY,
        status=StrategyStatus.DRAFT,
        source_document_id=document.id,
        created_by_id=test_user.id,
        extraction_confidence=0.9,
    )
    db_session.add(strategy)
    await db_session.commit()

    # Try to update without auth
    code_data = {"code": "def test(): pass", "code_language": "python"}
    
    response = await client.put(
        f"/api/v1/strategies/{strategy.id}/code",
        json=code_data,
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_strategy_code_forbidden(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    auth_headers: dict,
):
    """Test updating another user's strategy code."""
    # Create another user
    other_user = User(
        email="other@example.com",
        username="otheruser",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.flush()

    # Create a document for the other user
    document = Document(
        filename="other.pdf",
        file_path="/path/to/other.pdf",
        file_size=1024,
        mime_type="application/pdf",
        status=DocumentStatus.PROCESSED,
        uploaded_by_id=other_user.id,
    )
    db_session.add(document)
    await db_session.flush()

    # Create a strategy owned by the other user
    strategy = Strategy(
        name="Other User Strategy",
        description="Test description",
        asset_class=AssetClass.EQUITY,
        status=StrategyStatus.DRAFT,
        source_document_id=document.id,
        created_by_id=other_user.id,
        extraction_confidence=0.9,
    )
    db_session.add(strategy)
    await db_session.commit()

    # Try to update as test_user
    code_data = {"code": "def test(): pass", "code_language": "python"}
    
    response = await client.put(
        f"/api/v1/strategies/{strategy.id}/code",
        json=code_data,
        headers=auth_headers,
    )
    
    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_strategy_code_not_found(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test updating code for non-existent strategy."""
    code_data = {"code": "def test(): pass", "code_language": "python"}
    
    response = await client.put(
        "/api/v1/strategies/99999/code",
        json=code_data,
        headers=auth_headers,
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_strategy_code_preserves_other_fields(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    auth_headers: dict,
):
    """Test that updating code doesn't affect other fields."""
    # Create a test document
    document = Document(
        filename="test.pdf",
        file_path="/path/to/test.pdf",
        file_size=1024,
        mime_type="application/pdf",
        status=DocumentStatus.PROCESSED,
        uploaded_by_id=test_user.id,
    )
    db_session.add(document)
    await db_session.flush()

    # Create a test strategy with all fields
    strategy = Strategy(
        name="Test Strategy",
        description="Original description",
        asset_class=AssetClass.EQUITY,
        status=StrategyStatus.VALIDATED,
        parameters={"param1": "value1"},
        entry_rules={"rule1": "entry"},
        exit_rules={"rule1": "exit"},
        risk_parameters={"max_risk": 0.02},
        expected_return=0.15,
        sharpe_ratio=1.2,
        source_document_id=document.id,
        created_by_id=test_user.id,
        extraction_confidence=0.9,
    )
    db_session.add(strategy)
    await db_session.commit()

    # Update only the code
    code_data = {"code": "# New implementation", "code_language": "python"}
    
    response = await client.put(
        f"/api/v1/strategies/{strategy.id}/code",
        json=code_data,
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that code was updated
    assert data["code"] == code_data["code"]
    assert data["code_language"] == "python"
    
    # Check that other fields remain unchanged
    assert data["name"] == "Test Strategy"
    assert data["description"] == "Original description"
    assert data["status"] == "validated"
    assert data["parameters"] == {"param1": "value1"}
    assert data["expected_return"] == 0.15
    assert data["sharpe_ratio"] == 1.2