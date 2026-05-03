"""Add partial index on prices.promo_ends_at for cleanup queries.

Revision ID: h2c3d4e5f6g7
Revises: h1a2b3c4d5e6
Create Date: 2026-05-04

The hourly promo expiry cleanup filters by
    promo_ends_at IS NOT NULL AND promo_ends_at < now() AND promo_price_nzd IS NOT NULL
With no supporting index, Postgres falls back to a sequential scan of `prices`,
which times out under degraded Supabase IO. A partial b-tree on promo_ends_at
keeps the hot path (only rows that *have* a promo_ends_at) tiny and ordered.

CONCURRENTLY so we don't lock writes on the prices table during creation.
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op


revision: str = "h2c3d4e5f6g7"
down_revision: Union[str, Sequence[str], None] = "h1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # CREATE INDEX CONCURRENTLY cannot run inside a transaction.
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_price_promo_ends_at_partial",
            "prices",
            ["promo_ends_at"],
            unique=False,
            postgresql_concurrently=True,
            postgresql_where=sa.text("promo_ends_at IS NOT NULL"),
            if_not_exists=True,
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index(
            "ix_price_promo_ends_at_partial",
            table_name="prices",
            postgresql_concurrently=True,
            if_exists=True,
        )
