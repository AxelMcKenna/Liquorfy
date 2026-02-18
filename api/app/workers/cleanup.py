"""
Periodic promo expiry cleanup.

NULLs promo fields on Price rows where promo_ends_at is set and in the past.
Designed to run hourly (lightweight single UPDATE, no scraping).
"""
from __future__ import annotations

import logging

from sqlalchemy import func, update

from app.db.models import Price
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


__all__ = ["run_promo_expiry_cleanup"]
