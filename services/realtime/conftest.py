from unittest.mock import AsyncMock

import pytest
from config.database import get_db
from config.redis import get_redis
from httpx import ASGITransport, AsyncClient
from main import app
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = AsyncMock(spec=Redis)
    # Mock publish to return integer (number of clients received)
    mock.publish.return_value = 1
    return mock


@pytest.fixture
def mock_db_session():
    """Mock Database Session."""
    mock = AsyncMock(spec=AsyncSession)
    return mock


@pytest.fixture(autouse=True)
def override_dependencies(mock_redis, mock_db_session):
    """Override FastAPI dependencies with mocks."""
    app.dependency_overrides[get_redis] = lambda: mock_redis
    app.dependency_overrides[get_db] = lambda: mock_db_session
    yield
    app.dependency_overrides = {}


@pytest.fixture
async def client(override_dependencies):
    """AsyncClient for testing API endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def websocket_client():
    """TestClient for WebSockets (using Starlette's TestClient usually, checking alternatives)."""
    # FastAPI/Starlette TestClient (synchronous) is usually easier for WebSockets than httpx AsyncClient.
    # However, since we are in async mode, we might want to use AsyncClient if supported?
    # Actually, Starlette's TestClient is standard for WebSockets.
    # But wait, we are using async fixtures.
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        yield client
