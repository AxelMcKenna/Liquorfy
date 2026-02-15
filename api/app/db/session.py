from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncIterator, Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()

_TRUTHY = {"1", "true", "yes", "on"}

def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in _TRUTHY

def _adapt_urls(raw_url: str) -> tuple[URL, URL, dict[str, Any], dict[str, Any]]:
    """
    Return (async_url, sync_url, async_connect_args, sync_connect_args) with correct drivers set.
    Handles PostgreSQL and falls back to given URL for others.
    """
    url = make_url(raw_url)

    # PostgreSQL: prefer asyncpg for async, psycopg for sync
    if url.get_backend_name() in {"postgresql", "postgres"}:
        query = dict(url.query)
        sslmode = query.get("sslmode")
        pgbouncer = query.get("pgbouncer")

        async_query = dict(query)
        async_query.pop("sslmode", None)
        async_query.pop("pgbouncer", None)

        sync_query = dict(query)
        sync_query.pop("pgbouncer", None)

        async_connect_args: dict[str, Any] = {}
        sync_connect_args: dict[str, Any] = {}

        # Supabase (and many managed Postgres) require SSL. asyncpg needs ssl=True.
        if sslmode and sslmode.lower() in {"require", "verify-ca", "verify-full"}:
            async_connect_args["ssl"] = True

        # PgBouncer/Supavisor transaction pooling: disable prepared statements.
        if _is_truthy(pgbouncer):
            async_connect_args.setdefault("statement_cache_size", 0)
            sync_connect_args.setdefault("prepare_threshold", 0)

        async_url = url.set(drivername="postgresql+asyncpg", query=async_query)
        # If you want psycopg3; use "+psycopg". For psycopg2 use "+psycopg2".
        sync_url = url.set(drivername="postgresql+psycopg", query=sync_query)
        return async_url, sync_url, async_connect_args, sync_connect_args

    # SQLite or anything else: just reuse as-is
    return url, url, {}, {}

_async_url, _sync_url, _async_connect_args, _sync_connect_args = _adapt_urls(_settings.database_url)

# Tweak these via settings if you want
ECHO = _settings.environment == "development"
POOL_PRE_PING = True
# Connection pool settings - tune based on available RAM:
# - 1GB RAM: pool_size=10, max_overflow=10 (~20 max connections)
# - 2GB RAM: pool_size=20, max_overflow=20 (~40 max connections)
# - 4GB+ RAM: pool_size=30, max_overflow=30 (~60 max connections)
POOL_SIZE = getattr(_settings, "db_pool_size", 10)
MAX_OVERFLOW = getattr(_settings, "db_max_overflow", 10)
POOL_TIMEOUT = getattr(_settings, "db_pool_timeout", 30)
POOL_RECYCLE = getattr(_settings, "db_pool_recycle", 1800)  # Recycle connections after 30 min

# Engines
_async_engine = create_async_engine(
    _async_url,
    echo=ECHO,
    connect_args=_async_connect_args,
    pool_pre_ping=POOL_PRE_PING,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    future=True,
)

_sync_engine = create_engine(
    _sync_url,
    echo=ECHO,
    connect_args=_sync_connect_args,
    pool_pre_ping=POOL_PRE_PING,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
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
