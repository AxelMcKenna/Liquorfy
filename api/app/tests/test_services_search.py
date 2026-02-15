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
    assert "order by coalesce(prices.promo_price_nzd, prices.price_nzd) asc" in rownum_window
    assert "order by ((prices.price_nzd - coalesce" not in rownum_window
