from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def record_product_view(session: AsyncSession, product_id: UUID) -> None:
    """Upsert a view count for a product (INSERT ON CONFLICT DO UPDATE)."""
    await session.execute(
        text("""
            INSERT INTO product_views (product_id, view_count, last_viewed_at)
            VALUES (:pid, 1, :now)
            ON CONFLICT (product_id)
            DO UPDATE SET
                view_count = product_views.view_count + 1,
                last_viewed_at = :now
        """),
        {"pid": product_id, "now": datetime.now(tz=timezone.utc)},
    )
