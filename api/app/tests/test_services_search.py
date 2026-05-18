"""Tests for search service SQL sorting behavior."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.queries import ProductQueryParams
from app.services.search import fetch_products


def _sql(statement) -> str:
    return str(statement.compile(compile_kwargs={"literal_binds": True})).lower()


@pytest.mark.asyncio
async def test_price_per_standard_drink_sort_uses_volume_and_abv() -> None:
    """Sort SQL should use standard drinks formula, not just ABV denominator."""
    captured_statements = []

    async def execute_side_effect(statement):
        captured_statements.append(statement)
        result = MagicMock()
        if len(captured_statements) == 1:
            result.scalar_one.return_value = 0
        else:
            result.all.return_value = []
        return result

    session = AsyncMock()
    session.execute = AsyncMock(side_effect=execute_side_effect)

    await fetch_products(
        session,
        ProductQueryParams(sort="price_per_standard_drink", page=1, page_size=20),
    )

    # Second execute call is the data query with ORDER BY.
    sql = _sql(captured_statements[1])
    assert "order by" in sql
    assert "total_volume_ml" in sql
    assert "abv_percent" in sql
    assert "nullif((products.total_volume_ml" in sql


@pytest.mark.asyncio
async def test_text_search_uses_materialized_ctes() -> None:
    """Text search must use the two-CTE pattern so the trigram + composite indexes get picked.

    Without `MATERIALIZED` the planner inlines the CTEs and reverts to a slow geo-first
    plan (5–17s on 1.4M rows). The materialized form runs in <1s.
    """
    captured_statements = []

    async def execute_side_effect(statement):
        captured_statements.append(statement)
        result = MagicMock()
        if len(captured_statements) == 1:
            result.scalar_one.return_value = 0
        else:
            result.all.return_value = []
        return result

    session = AsyncMock()
    session.execute = AsyncMock(side_effect=execute_side_effect)

    # Christchurch CBD
    await fetch_products(
        session,
        ProductQueryParams(
            q="johnnie walker",
            lat=-43.5321,
            lon=172.6362,
            radius_km=5,
            sort="relevance",
            page=1,
            page_size=20,
        ),
    )

    sql = _sql(captured_statements[0])
    # Both CTEs must be materialized and present
    assert "with " in sql
    assert "matching_products as materialized" in sql
    assert "nearby_stores as materialized" in sql
    # Trigram-friendly predicate: lower(name) LIKE, not ILIKE
    assert "lower(products.name) like '%johnnie walker%'" in sql
    assert " ilike " not in sql
    # Geo CTE uses ST_DWithin
    assert "st_dwithin" in sql


@pytest.mark.asyncio
async def test_text_search_without_location_still_uses_product_cte() -> None:
    """Locationless small text searches should still use the matching_products CTE."""
    captured_statements = []

    async def execute_side_effect(statement):
        captured_statements.append(statement)
        result = MagicMock()
        if len(captured_statements) == 1:
            result.scalar_one.return_value = 0
        else:
            result.all.return_value = []
        return result

    session = AsyncMock()
    session.execute = AsyncMock(side_effect=execute_side_effect)

    await fetch_products(
        session,
        ProductQueryParams(q="heineken", page=1, page_size=20, sort="relevance"),
    )

    sql = _sql(captured_statements[0])
    assert "matching_products as materialized" in sql
    assert "nearby_stores" not in sql


@pytest.mark.asyncio
async def test_unique_products_row_selection_uses_requested_sort() -> None:
    """unique_products row_number ordering should follow requested sort."""
    captured_statements = []

    async def execute_side_effect(statement):
        captured_statements.append(statement)
        result = MagicMock()
        if len(captured_statements) == 1:
            result.scalar_one.return_value = 0
        else:
            result.all.return_value = []
        return result

    session = AsyncMock()
    session.execute = AsyncMock(side_effect=execute_side_effect)

    await fetch_products(
        session,
        ProductQueryParams(unique_products=True, sort="total_price", page=1, page_size=20),
    )

    sql = _sql(captured_statements[1])
    rownum_start = sql.find("row_number() over")
    rownum_window = sql[rownum_start:rownum_start + 500]
    assert "order by coalesce(case when (prices.promo_price_nzd is not null and (prices.promo_ends_at is null or prices.promo_ends_at > now())) then prices.promo_price_nzd end, prices.price_nzd) asc" in rownum_window
    assert "order by ((prices.price_nzd - coalesce" not in rownum_window
