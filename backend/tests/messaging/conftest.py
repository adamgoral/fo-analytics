"""Common fixtures for messaging tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import aio_pika


@pytest.fixture
def mock_aio_pika_connection():
    """Mock aio-pika connection."""
    mock = AsyncMock(spec=aio_pika.RobustConnection)
    mock.is_closed = False
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_aio_pika_channel():
    """Mock aio-pika channel."""
    mock = AsyncMock(spec=aio_pika.RobustChannel)
    mock.is_closed = False
    mock.close = AsyncMock()
    mock.set_qos = AsyncMock()
    mock.declare_exchange = AsyncMock()
    mock.declare_queue = AsyncMock()
    return mock


@pytest.fixture
def mock_aio_pika_exchange():
    """Mock aio-pika exchange."""
    mock = AsyncMock(spec=aio_pika.Exchange)
    mock.publish = AsyncMock()
    return mock


@pytest.fixture
def mock_aio_pika_queue():
    """Mock aio-pika queue."""
    mock = AsyncMock()
    mock.bind = AsyncMock()
    mock.iterator = AsyncMock()
    return mock


@pytest.fixture
def mock_aio_pika_message():
    """Mock aio-pika message."""
    mock = MagicMock(spec=aio_pika.Message)
    mock.body = b'{"test": "data"}'
    mock.content_type = "application/json"
    mock.delivery_mode = aio_pika.DeliveryMode.PERSISTENT
    mock.message_id = str(uuid4())
    mock.correlation_id = None
    return mock


@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "document_id": uuid4(),
        "user_id": uuid4(),
        "file_key": "user123/document456.pdf",
        "filename": "test_strategy.pdf",
        "file_size": 1048576,
        "content_type": "application/pdf",
        "processing_type": "full"
    }


@pytest.fixture
def sample_processing_result():
    """Sample processing result for testing."""
    return {
        "extracted_text": "This is a test document with investment strategies.",
        "strategies": [
            {
                "name": "Growth Strategy",
                "description": "Focus on high-growth stocks",
                "allocation": "60%"
            },
            {
                "name": "Income Strategy",
                "description": "Focus on dividend-paying stocks",
                "allocation": "40%"
            }
        ],
        "metadata": {
            "pages": 5,
            "title": "Investment Strategy Document",
            "author": "Test Author"
        }
    }