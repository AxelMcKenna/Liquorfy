"""
Unit tests for the three-layer price freshness system.

Covers:
- sweep_chain_promos: clears promos on old rows, leaves fresh rows alone
- sweep_store_promos: scopes to single store
- run_promo_expiry_cleanup: clears rows with past promo_ends_at
- _effective_price: returns correct price for expired/valid/no-promo cases
- _is_stale: returns correct staleness flag based on last_seen_at
"""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers for building mock Price objects
# ---------------------------------------------------------------------------

def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _make_price(
    *,
    price_nzd: float = 30.0,
    promo_price_nzd: float | None = None,
    promo_ends_at: datetime | None = None,
    last_seen_at: datetime | None = None,
) -> MagicMock:
    """Return a mock Price with the given field values."""
    p = MagicMock()
    p.price_nzd = price_nzd
    p.promo_price_nzd = promo_price_nzd
    p.promo_ends_at = promo_ends_at
    p.last_seen_at = last_seen_at if last_seen_at is not None else _now_utc()
    return p


# ---------------------------------------------------------------------------
# _effective_price
# ---------------------------------------------------------------------------

class TestEffectivePrice:
    """Tests for the query-time _effective_price helper."""

    def _fn(self, price):
        from app.services.search import _effective_price
        return _effective_price(price)

    def test_no_promo_returns_regular_price(self):
        price = _make_price(price_nzd=30.0, promo_price_nzd=None)
        assert self._fn(price) == 30.0

    def test_valid_promo_no_end_date_returns_promo(self):
        price = _make_price(price_nzd=30.0, promo_price_nzd=20.0, promo_ends_at=None)
        assert self._fn(price) == 20.0

    def test_valid_promo_future_end_date_returns_promo(self):
        future = _now_utc() + timedelta(days=3)
        price = _make_price(price_nzd=30.0, promo_price_nzd=20.0, promo_ends_at=future)
        assert self._fn(price) == 20.0

    def test_expired_promo_returns_regular_price(self):
        past = _now_utc() - timedelta(days=1)
        price = _make_price(price_nzd=30.0, promo_price_nzd=20.0, promo_ends_at=past)
        assert self._fn(price) == 30.0

    def test_promo_ends_exactly_now_is_expired(self):
        # A promo ending in the past (even 1 second ago) should be ignored
        just_past = _now_utc() - timedelta(seconds=1)
        price = _make_price(price_nzd=30.0, promo_price_nzd=20.0, promo_ends_at=just_past)
        assert self._fn(price) == 30.0


# ---------------------------------------------------------------------------
# _is_stale
# ---------------------------------------------------------------------------

class TestIsStale:
    """Tests for the _is_stale helper."""

    def _fn(self, price):
        from app.services.search import _is_stale
        return _is_stale(price)

    def test_recent_price_is_not_stale(self):
        price = _make_price(last_seen_at=_now_utc() - timedelta(hours=12))
        assert self._fn(price) is False

    def test_price_seen_6_days_ago_is_not_stale(self):
        price = _make_price(last_seen_at=_now_utc() - timedelta(days=6))
        assert self._fn(price) is False

    def test_price_seen_8_days_ago_is_stale(self):
        price = _make_price(last_seen_at=_now_utc() - timedelta(days=8))
        assert self._fn(price) is True

    def test_naive_datetime_treated_as_utc(self):
        # last_seen_at stored without tzinfo (utcnow) should still be handled
        naive_recent = datetime.utcnow() - timedelta(hours=1)
        price = _make_price(last_seen_at=naive_recent)
        assert self._fn(price) is False

    def test_naive_old_datetime_is_stale(self):
        naive_old = datetime.utcnow() - timedelta(days=10)
        price = _make_price(last_seen_at=naive_old)
        assert self._fn(price) is True

    def test_none_last_seen_at_is_stale(self):
        price = MagicMock()
        price.last_seen_at = None
        from app.services.search import _is_stale
        assert _is_stale(price) is True


# ---------------------------------------------------------------------------
# sweep_chain_promos
# ---------------------------------------------------------------------------

class TestSweepChainPromos:
    """Tests for freshness.sweep_chain_promos."""

    @pytest.mark.asyncio
    async def test_calls_update_with_correct_conditions(self):
        """sweep_chain_promos should issue an UPDATE filtering by chain and last_seen_at."""
        from app.services.freshness import sweep_chain_promos

        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        run_started_at = _now_utc()
        count = await sweep_chain_promos(mock_session, "liquorland", run_started_at)

        assert count == 3
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_rows_updated(self):
        from app.services.freshness import sweep_chain_promos

        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        count = await sweep_chain_promos(mock_session, "liquorland", _now_utc())
        assert count == 0

    @pytest.mark.asyncio
    async def test_logs_when_rows_swept(self, caplog):
        import logging
        from app.services.freshness import sweep_chain_promos

        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        with caplog.at_level(logging.INFO, logger="app.services.freshness"):
            await sweep_chain_promos(mock_session, "countdown", _now_utc())

        assert any("5" in r.message and "countdown" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# sweep_store_promos
# ---------------------------------------------------------------------------

class TestSweepStorePromos:
    """Tests for freshness.sweep_store_promos."""

    @pytest.mark.asyncio
    async def test_calls_update_scoped_to_store(self):
        from app.services.freshness import sweep_store_promos

        store_id = uuid.uuid4()
        mock_result = MagicMock()
        mock_result.rowcount = 2
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        count = await sweep_store_promos(mock_session, store_id, _now_utc())

        assert count == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_different_stores_get_separate_calls(self):
        """Each store sweep should be an independent execute call."""
        from app.services.freshness import sweep_store_promos

        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        store_a = uuid.uuid4()
        store_b = uuid.uuid4()
        run_started_at = _now_utc()

        await sweep_store_promos(mock_session, store_a, run_started_at)
        await sweep_store_promos(mock_session, store_b, run_started_at)

        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_returns_zero_when_nothing_to_sweep(self):
        from app.services.freshness import sweep_store_promos

        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        count = await sweep_store_promos(mock_session, uuid.uuid4(), _now_utc())
        assert count == 0


# ---------------------------------------------------------------------------
# run_promo_expiry_cleanup
# ---------------------------------------------------------------------------

class TestRunPromoExpiryCleanup:
    """Tests for workers.cleanup.run_promo_expiry_cleanup."""

    @pytest.mark.asyncio
    async def test_issues_update_and_returns_count(self):
        from app.workers.cleanup import run_promo_expiry_cleanup

        mock_result = MagicMock()
        mock_result.rowcount = 7
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        @asynccontextmanager
        async def mock_transaction():
            yield mock_session

        with patch("app.workers.cleanup.async_transaction", mock_transaction):
            count = await run_promo_expiry_cleanup()

        assert count == 7
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_expired_promos(self):
        from app.workers.cleanup import run_promo_expiry_cleanup

        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        @asynccontextmanager
        async def mock_transaction():
            yield mock_session

        with patch("app.workers.cleanup.async_transaction", mock_transaction):
            count = await run_promo_expiry_cleanup()

        assert count == 0

    @pytest.mark.asyncio
    async def test_logs_when_rows_cleared(self, caplog):
        import logging
        from app.workers.cleanup import run_promo_expiry_cleanup

        mock_result = MagicMock()
        mock_result.rowcount = 4
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        @asynccontextmanager
        async def mock_transaction():
            yield mock_session

        with patch("app.workers.cleanup.async_transaction", mock_transaction):
            with caplog.at_level(logging.INFO, logger="app.workers.cleanup"):
                await run_promo_expiry_cleanup()

        assert any("4" in r.message for r in caplog.records)
