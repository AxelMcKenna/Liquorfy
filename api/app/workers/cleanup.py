"""
Periodic promo expiry cleanup.

NULLs promo fields on Price rows where promo_ends_at is set and in the past.
Designed to run every cycle from the worker (lightweight, no scraping).

Both functions paginate by ID and commit each batch in its own transaction so
that one timed-out batch does not roll back earlier progress, and so each
individual UPDATE / DELETE statement stays under Supabase's statement timeout.
"""
from __future__ import annotations

import logging

from sqlalchemy import delete, func, select, text, update

from app.db.models import Price, PriceHistory
from app.db.session import async_transaction

logger = logging.getLogger(__name__)

_BATCH_SIZE = 1000


async def run_promo_expiry_cleanup() -> int:
    """Clear promo fields on Price rows whose promo has expired.

    Returns:
        Number of rows updated.
    """
    total = 0
    while True:
        async with async_transaction() as session:
            ids = (
                await session.execute(
                    select(Price.id)
                    .where(
                        Price.promo_ends_at.is_not(None),
                        Price.promo_ends_at < func.now(),
                        Price.promo_price_nzd.is_not(None),
                    )
                    .limit(_BATCH_SIZE)
                )
            ).scalars().all()
            if not ids:
                break
            await session.execute(
                update(Price)
                .where(Price.id.in_(ids))
                .values(
                    promo_price_nzd=None,
                    promo_text=None,
                    promo_ends_at=None,
                )
            )
            total += len(ids)
        if len(ids) < _BATCH_SIZE:
            break

    if total:
        logger.info(f"Promo expiry cleanup: cleared {total} expired promo(s)")
    return total


async def run_price_history_cleanup(retention_days: int = 30) -> int:
    """Delete price_history rows older than retention_days.

    Returns:
        Number of rows deleted.
    """
    total = 0
    while True:
        async with async_transaction() as session:
            ids = (
                await session.execute(
                    select(PriceHistory.id)
                    .where(
                        PriceHistory.recorded_at
                        < func.now() - text(f"interval '{retention_days} days'"),
                    )
                    .limit(_BATCH_SIZE)
                )
            ).scalars().all()
            if not ids:
                break
            await session.execute(
                delete(PriceHistory).where(PriceHistory.id.in_(ids))
            )
            total += len(ids)
        if len(ids) < _BATCH_SIZE:
            break

    if total:
        logger.info(
            f"Price history cleanup: deleted {total} row(s) older than {retention_days} days"
        )
    return total


__all__ = ["run_promo_expiry_cleanup", "run_price_history_cleanup"]
