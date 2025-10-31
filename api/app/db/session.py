from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncIterator, Iterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()

_async_engine = create_async_engine(
    _settings.database_url.replace("postgresql+psycopg", "postgresql+asyncpg"),
    future=True,
    echo=_settings.environment == "development",
)
_async_session_factory = async_sessionmaker(_async_engine, expire_on_commit=False)

_sync_engine = _async_engine.sync_engine
_session_factory = sessionmaker(bind=_sync_engine, expire_on_commit=False)


@asynccontextmanager
def get_async_session() -> AsyncIterator[AsyncSession]:
    async with _async_session_factory() as session:
        yield session


@contextmanager
def get_session() -> Iterator[Session]:
    with _session_factory() as session:
        yield session


__all__ = ["get_async_session", "get_session", "_async_engine", "_sync_engine"]
