from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncIterator, Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url, URL
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()

def _adapt_urls(raw_url: str) -> tuple[URL, URL]:
    """
    Return (async_url, sync_url) with correct drivers set.
    Handles PostgreSQL and falls back to given URL for others.
    """
    url = make_url(raw_url)

    # PostgreSQL: prefer asyncpg for async, psycopg for sync
    if url.get_backend_name() in {"postgresql", "postgres"}:
        async_url = url.set(drivername="postgresql+asyncpg")
        # If you want psycopg3; use "+psycopg". For psycopg2 use "+psycopg2".
        sync_url = url.set(drivername="postgresql+psycopg")
        return async_url, sync_url

    # SQLite or anything else: just reuse as-is
    return url, url

_async_url, _sync_url = _adapt_urls(_settings.database_url)

# Tweak these via settings if you want
ECHO = _settings.environment == "development"
POOL_PRE_PING = True
POOL_SIZE = getattr(_settings, "db_pool_size", 5)
MAX_OVERFLOW = getattr(_settings, "db_max_overflow", 10)
POOL_TIMEOUT = getattr(_settings, "db_pool_timeout", 30)

# Engines
_async_engine = create_async_engine(
    _async_url,
    echo=ECHO,
    pool_pre_ping=POOL_PRE_PING,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    future=True,
)

_sync_engine = create_engine(
    _sync_url,
    echo=ECHO,
    pool_pre_ping=POOL_PRE_PING,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    future=True,
)

# Session factories
_async_session_factory = async_sessionmaker(
    bind=_async_engine,
    expire_on_commit=False,
    autoflush=False,
)

_session_factory = sessionmaker(
    bind=_sync_engine,
    expire_on_commit=False,
    autoflush=False,
)

# --- Plain "hand-me-a-session" dependencies (caller manages commit/rollback) ---

@asynccontextmanager
async def get_async_session() -> AsyncIterator[AsyncSession]:
    async with _async_session_factory() as session:
        try:
            yield session
        finally:
            # ensuring close() is awaited in case callers keep connections open
            await session.close()

@contextmanager
def get_session() -> Iterator[Session]:
    with _session_factory() as session:
        yield session  # contextmanager closes it automatically

# --- Transactional helpers (auto-commit / rollback) ---

@asynccontextmanager
async def async_transaction() -> AsyncIterator[AsyncSession]:
    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@contextmanager
def transaction() -> Iterator[Session]:
    with _session_factory() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

# --- FastAPI lifespan glue (optional) ---

async def dispose_engines() -> None:
    """Call on application shutdown to cleanly close pools."""
    await _async_engine.dispose()
    _sync_engine.dispose()

__all__ = [
    "get_async_session",
    "get_session",
    "async_transaction",
    "transaction",
    "dispose_engines",
    "_async_engine",
    "_sync_engine",
]
