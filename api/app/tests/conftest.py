"""Test fixtures and configuration for Liquorfy API tests."""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def pytest_configure(config):
    """Set up environment variables before any test imports happen."""
    os.environ["SECRET_KEY"] = "test-secret-key-that-is-at-least-32-chars-long"
    os.environ["ADMIN_USERNAME"] = "testadmin"
    os.environ["ADMIN_PASSWORD"] = "testpassword123"
    os.environ["ENVIRONMENT"] = "development"  # Use development for CORS
    os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:postgres@localhost:5432/liquorfy_test"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    os.environ["CORS_ORIGINS"] = "http://localhost:5173"

    # Clear any cached settings
    try:
        from app.core.config import get_settings
        get_settings.cache_clear()
    except ImportError:
        pass


# Import after environment is configured
from contextlib import asynccontextmanager

from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import IngestionRun, Price, Product, Store


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_engine():
    """Create an async SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine) -> AsyncIterator[AsyncSession]:
    """Create an async session for testing."""
    factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
def mock_redis():
    """Mock Redis client for tests."""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.setex = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    mock.ping = AsyncMock(return_value=True)
    mock.close = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def client(mock_redis) -> Iterator[TestClient]:
    """Create a test client with mocked dependencies."""
    # Clear settings cache first
    from app.core.config import get_settings
    get_settings.cache_clear()

    # Mock database session
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar=MagicMock(return_value=1)))
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    @asynccontextmanager
    async def mock_transaction():
        yield mock_session

    with patch("app.db.session.get_async_session", mock_get_session):
        with patch("app.db.session.async_transaction", mock_transaction):
            with patch("app.routes.health.async_transaction", mock_transaction):
                with patch("app.routes.products.get_async_session", mock_get_session):
                    with patch("app.routes.stores.get_async_session", mock_get_session):
                        with patch("app.routes.worker.get_async_session", mock_get_session):
                            # Mock Redis
                            async def mock_get_redis():
                                return mock_redis

                            with patch("app.core.auth.get_redis_client", mock_get_redis):
                                with patch("app.routes.health.redis.from_url", return_value=mock_redis):
                                    with patch("app.services.cache._cache._redis", mock_redis):
                                        from app.main import app
                                        with TestClient(app) as test_client:
                                            yield test_client


@pytest.fixture
async def async_client(mock_redis) -> AsyncIterator[AsyncClient]:
    """Create an async test client."""
    with patch("app.core.auth.get_redis_client", return_value=mock_redis):
        with patch("app.routes.health.redis.from_url", return_value=mock_redis):
            with patch("app.services.cache._cache._redis", mock_redis):
                from app.core.config import get_settings
                get_settings.cache_clear()

                from app.main import app
                async with AsyncClient(app=app, base_url="http://test") as ac:
                    yield ac


# Sample test data fixtures
@pytest.fixture
def sample_store_id() -> uuid.UUID:
    """Generate a sample store UUID."""
    return uuid.uuid4()


@pytest.fixture
def sample_product_id() -> uuid.UUID:
    """Generate a sample product UUID."""
    return uuid.uuid4()


@pytest.fixture
def sample_store(sample_store_id) -> Store:
    """Create a sample store for testing."""
    return Store(
        id=sample_store_id,
        name="Test Store",
        chain="test_chain",
        lat=-36.8485,
        lon=174.7633,
        address="123 Test St, Auckland",
        region="Auckland",
    )


@pytest.fixture
def sample_product(sample_product_id) -> Product:
    """Create a sample product for testing."""
    return Product(
        id=sample_product_id,
        chain="test_chain",
        source_product_id="TEST123",
        name="Test Beer 12x330ml",
        brand="Test Brand",
        category="beer",
        abv_percent=5.0,
        pack_count=12,
        unit_volume_ml=330.0,
        total_volume_ml=3960.0,
        image_url="https://example.com/test.jpg",
        product_url="https://example.com/product",
    )


@pytest.fixture
def sample_price(sample_product_id, sample_store_id) -> Price:
    """Create a sample price for testing."""
    now = datetime.utcnow()
    return Price(
        id=uuid.uuid4(),
        product_id=sample_product_id,
        store_id=sample_store_id,
        currency="NZD",
        price_nzd=29.99,
        promo_price_nzd=24.99,
        promo_text="On special!",
        promo_ends_at=now + timedelta(days=7),
        last_seen_at=now,
        price_last_changed_at=now,
        is_member_only=False,
    )


@pytest.fixture
def sample_ingestion_run() -> IngestionRun:
    """Create a sample ingestion run for testing."""
    now = datetime.utcnow()
    return IngestionRun(
        id=uuid.uuid4(),
        chain="test_chain",
        status="completed",
        started_at=now - timedelta(hours=1),
        finished_at=now,
        items_total=100,
        items_changed=50,
        items_failed=2,
    )


@pytest.fixture
def auth_token() -> str:
    """Generate a valid admin auth token for testing."""
    from app.core.auth import create_admin_token
    return create_admin_token()


@pytest.fixture
def auth_headers(auth_token) -> dict[str, str]:
    """Create auth headers with valid token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def invalid_auth_headers() -> dict[str, str]:
    """Create auth headers with invalid token."""
    return {"Authorization": "Bearer invalid-token"}


# Settings fixtures
@pytest.fixture
def test_settings():
    """Get test settings."""
    from app.core.config import get_settings
    get_settings.cache_clear()
    return get_settings()
