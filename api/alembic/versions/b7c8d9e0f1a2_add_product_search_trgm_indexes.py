"""Add trigram indexes for product text search

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-02-15

Adds PostgreSQL pg_trgm GIN indexes for case-insensitive substring search
on products.name and products.brand. These indexes accelerate queries using:
- lower(products.name) LIKE '%term%'
- lower(products.brand) LIKE '%term%'
"""
from typing import Sequence, Union

from alembic import op


revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create pg_trgm extension and product text search indexes."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_products_name_trgm
        ON products USING gin (lower(name) gin_trgm_ops)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_products_brand_trgm
        ON products USING gin (lower(brand) gin_trgm_ops)
        WHERE brand IS NOT NULL
        """
    )


def downgrade() -> None:
    """Drop product text search indexes."""
    op.execute("DROP INDEX IF EXISTS ix_products_brand_trgm")
    op.execute("DROP INDEX IF EXISTS ix_products_name_trgm")
