"""Add unique price constraint on (product_id, store_id) with dedupe.

Revision ID: c4d5e6f7a8b9
Revises: b7c8d9e0f1a2
Create Date: 2026-02-21 12:05:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    # Remove duplicate rows first, keeping the freshest row per (product_id, store_id).
    op.execute(
        sa.text(
            """
            WITH ranked AS (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY product_id, store_id
                        ORDER BY
                            last_seen_at DESC NULLS LAST,
                            updated_at DESC NULLS LAST,
                            created_at DESC NULLS LAST,
                            id DESC
                    ) AS rn
                FROM prices
            )
            DELETE FROM prices p
            USING ranked r
            WHERE p.id = r.id
              AND r.rn > 1;
            """
        )
    )

    inspector = sa.inspect(conn)
    index_names = {idx["name"] for idx in inspector.get_indexes("prices")}
    if "ix_price_product_store" in index_names:
        op.drop_index("ix_price_product_store", table_name="prices")

    unique_names = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("prices")
    }
    if "uq_price_product_store" not in unique_names:
        op.create_unique_constraint(
            "uq_price_product_store",
            "prices",
            ["product_id", "store_id"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    unique_names = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("prices")
    }
    if "uq_price_product_store" in unique_names:
        op.drop_constraint("uq_price_product_store", "prices", type_="unique")

    index_names = {idx["name"] for idx in inspector.get_indexes("prices")}
    if "ix_price_product_store" not in index_names:
        op.create_index("ix_price_product_store", "prices", ["product_id", "store_id"])
