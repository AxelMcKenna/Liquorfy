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


_SWEEP_BATCH_SIZE = 1000


async def sweep_chain_promos(
    session: AsyncSession,
    chain: str,
    run_started_at: datetime,
) -> int:
    """Clear promo fields on Price rows not seen in the current chain-wide run.

    Paginated by ID to keep each UPDATE statement under Supabase's statement
    timeout, even when many rows match (Supabase disk IO can be slow during
    incidents).

    Args:
        session: Active async DB session (caller manages commit).
        chain: Chain identifier (e.g. "liquorland").
        run_started_at: Timestamp captured at the start of the scraper run.

    Returns:
        Number of rows updated.
    """
    total = 0
    while True:
        ids = (
            await session.execute(
                select(Price.id)
                .where(
                    Price.store_id.in_(
                        select(Store.id).where(Store.chain == chain)
                    ),
                    Price.last_seen_at < run_started_at,
                    Price.promo_price_nzd.is_not(None),
                )
                .limit(_SWEEP_BATCH_SIZE)
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
        if len(ids) < _SWEEP_BATCH_SIZE:
            break
    if total:
        logger.info(f"Swept {total} stale promo(s) for chain={chain}")
    return total


async def sweep_store_promos(
    session: AsyncSession,
    store_id: UUID,
    run_started_at: datetime,
) -> int:
    """Clear promo fields on Price rows not seen in the current per-store run.

    Paginated by ID to keep each UPDATE statement under Supabase's statement
    timeout, even when many rows match.

    Args:
        session: Active async DB session (caller manages commit).
        store_id: UUID of the store that was just scraped.
        run_started_at: Timestamp captured at the start of the scraper run.

    Returns:
        Number of rows updated.
    """
    total = 0
    while True:
        ids = (
            await session.execute(
                select(Price.id)
                .where(
                    Price.store_id == store_id,
                    Price.last_seen_at < run_started_at,
                    Price.promo_price_nzd.is_not(None),
                )
                .limit(_SWEEP_BATCH_SIZE)
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
        if len(ids) < _SWEEP_BATCH_SIZE:
            break
    if total:
        logger.info(f"Swept {total} stale promo(s) for store_id={store_id}")
    return total


__all__ = ["sweep_chain_promos", "sweep_store_promos"]
