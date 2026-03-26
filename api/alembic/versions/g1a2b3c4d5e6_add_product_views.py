"""Add product_views table for popularity tracking.

Revision ID: g1a2b3c4d5e6
Revises: f8a9b0c1d2e3
Create Date: 2026-03-26 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "g1a2b3c4d5e6"
down_revision: Union[str, None] = "f8a9b0c1d2e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_views",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_viewed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_product_views_count", "product_views", ["view_count"])


def downgrade() -> None:
    op.drop_index("ix_product_views_count", table_name="product_views")
    op.drop_table("product_views")
