"""Add canonical_product_id to products for cross-chain matching.

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
Create Date: 2026-03-26 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f8a9b0c1d2e3"
down_revision: Union[str, None] = "e7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("canonical_product_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_product_canonical",
        "products",
        ["canonical_product_id"],
        postgresql_where=sa.text("canonical_product_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_product_canonical", table_name="products")
    op.drop_column("products", "canonical_product_id")
