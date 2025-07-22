# Repository Pattern Implementation

This directory contains the repository pattern implementation for the Front Office Analytics platform.

## Architecture

The repository pattern provides a layer of abstraction between the domain models and data access logic. This implementation follows Domain-Driven Design (DDD) principles and provides:

1. **Separation of Concerns**: Business logic is separated from data access logic
2. **Testability**: Easy to mock repositories for unit testing
3. **Flexibility**: Easy to switch data sources without changing business logic
4. **Type Safety**: Full type hints with generics support

## Structure

```
repositories/
├── base.py           # Generic base repository with CRUD operations
├── user.py           # User-specific repository
├── document.py       # Document-specific repository
├── strategy.py       # Strategy-specific repository
├── backtest.py       # Backtest-specific repository
└── unit_of_work.py   # Transaction management across repositories
```

## Usage Examples

### Basic Repository Usage

```python
from src.core.dependencies import get_user_repository

# In an API endpoint
async def get_user(
    user_id: UUID,
    user_repo: UserRepository = Depends(get_user_repository)
):
    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404)
    return user
```

### Unit of Work Pattern

For operations that span multiple repositories:

```python
from src.repositories.unit_of_work import UnitOfWork

async def create_user_with_document():
    async with UnitOfWork() as uow:
        # Create user
        user = await uow.users.create(
            email="user@example.com",
            username="testuser"
        )
        
        # Create related document
        document = await uow.documents.create(
            user_id=user.id,
            name="Initial Document"
        )
        
        # Commit transaction
        await uow.commit()
```

## Repository Methods

### Base Repository

All repositories inherit these methods:

- `get(id: UUID)` - Get a single record by ID
- `get_all(skip: int, limit: int)` - Get all records with pagination
- `create(**kwargs)` - Create a new record
- `update(id: UUID, **kwargs)` - Update an existing record
- `delete(id: UUID)` - Delete a record
- `exists(id: UUID)` - Check if a record exists

### Specialized Repositories

Each repository adds domain-specific methods:

**UserRepository**
- `get_by_email(email: str)`
- `get_by_username(username: str)`
- `get_active_users(skip: int, limit: int)`
- `activate_user(user_id: UUID)`
- `deactivate_user(user_id: UUID)`

**DocumentRepository**
- `get_by_user(user_id: UUID)`
- `get_by_status(status: str)`
- `get_pending_documents(limit: int)`
- `update_status(document_id: UUID, status: str)`

**StrategyRepository**
- `get_by_document(document_id: UUID)`
- `get_by_user(user_id: UUID)`
- `get_active_strategies(user_id: UUID)`
- `activate_strategy(strategy_id: UUID)`

**BacktestRepository**
- `get_by_strategy(strategy_id: UUID)`
- `get_by_status(status: str)`
- `get_pending_backtests(limit: int)`
- `mark_as_completed(backtest_id: UUID, metrics: dict)`

## Testing

Repositories are easily testable with the provided fixtures:

```python
@pytest.mark.asyncio
async def test_user_creation(async_session):
    repo = UserRepository(async_session)
    user = await repo.create(email="test@example.com")
    assert user.email == "test@example.com"
```

## Best Practices

1. **Use dependency injection**: Always inject repositories through FastAPI's dependency system
2. **Keep repositories thin**: Repositories should only contain data access logic
3. **Use services for business logic**: Complex business logic belongs in the service layer
4. **Transaction boundaries**: Use Unit of Work for operations spanning multiple repositories
5. **Type safety**: Always use type hints for better IDE support and catch errors early