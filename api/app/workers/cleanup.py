"""
Periodic promo expiry cleanup.

NULLs promo fields on Price rows where promo_ends_at is set and in the past.
Designed to run hourly (lightweight single UPDATE, no scraping).
"""
from __future__ import annotations

import logging

from sqlalchemy import delete, func, text, update

from app.db.models import Price, PriceHistory
from app.db.session import async_transaction

logger = logging.getLogger(__name__)


async def run_promo_expiry_cleanup() -> int:
    """Clear promo fields on Price rows whose promo has expired.

    Returns:
        Number of rows updated.
    """
    async with async_transaction() as session:
        stmt = (
            update(Price)
            .where(
                Price.promo_ends_at.is_not(None),
                Price.promo_ends_at < func.now(),
                Price.promo_price_nzd.is_not(None),
            )
            .values(
                promo_price_nzd=None,
                promo_text=None,
                promo_ends_at=None,
            )
        )
        result = await session.execute(stmt)
        count = getattr(result, "rowcount", 0) or 0

    if count:
        logger.info(f"Promo expiry cleanup: cleared {count} expired promo(s)")
    return count


async def run_price_history_cleanup(retention_days: int = 30) -> int:
    """Delete price_history rows older than retention_days.

    Returns:
        Number of rows deleted.
    """
    async with async_transaction() as session:
        stmt = (
            delete(PriceHistory)
            .where(
                PriceHistory.recorded_at < func.now() - text(f"interval '{retention_days} days'"),
            )
        )
        result = await session.execute(stmt)
        count = getattr(result, "rowcount", 0) or 0

    if count:
        logger.info(f"Price history cleanup: deleted {count} row(s) older than {retention_days} days")
    return count


__all__ = ["run_promo_expiry_cleanup", "run_price_history_cleanup"]
