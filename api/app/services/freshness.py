"""
Freshness sweep functions for clearing stale promo data.

After a successful scrape, products that were not seen in the current run
still have their old promo fields.  These functions NULL out promo columns
on Price rows whose last_seen_at is older than the run start time.
"""
from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Price, Store

logger = logging.getLogger(__name__)


async def sweep_chain_promos(
    session: AsyncSession,
    chain: str,
    run_started_at: datetime,
) -> int:
    """Clear promo fields on Price rows not seen in the current chain-wide run.

    Args:
        session: Active async DB session (caller manages commit).
        chain: Chain identifier (e.g. "liquorland").
        run_started_at: Timestamp captured at the start of the scraper run.

    Returns:
        Number of rows updated.
    """
    stmt = (
        update(Price)
        .where(
            Price.store_id.in_(select(Store.id).where(Store.chain == chain)),
            Price.last_seen_at < run_started_at,
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
        logger.info(f"Swept {count} stale promo(s) for chain={chain}")
    return count


async def sweep_store_promos(
    session: AsyncSession,
    store_id: UUID,
    run_started_at: datetime,
) -> int:
    """Clear promo fields on Price rows not seen in the current per-store run.

    Args:
        session: Active async DB session (caller manages commit).
        store_id: UUID of the store that was just scraped.
        run_started_at: Timestamp captured at the start of the scraper run.

    Returns:
        Number of rows updated.
    """
    stmt = (
        update(Price)
        .where(
            Price.store_id == store_id,
            Price.last_seen_at < run_started_at,
            Price.promo_price_nzd.is_not(None),
        )
        .values(
            promo_price_nzd=None,
            promo_text=None,
            promo_ends_at=None,
        )
    )
    result = await session.execute(stmt)
    count = result.rowcount
    if count:
        logger.info(f"Swept {count} stale promo(s) for store_id={store_id}")
    return count


__all__ = ["sweep_chain_promos", "sweep_store_promos"]
