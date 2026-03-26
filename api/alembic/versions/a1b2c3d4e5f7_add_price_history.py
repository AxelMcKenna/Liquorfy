"""Add price_history table for 30-day rolling price tracking.

Revision ID: a1b2c3d4e5f7
Revises: f8a9b0c1d2e3
Create Date: 2026-03-26 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f7"
down_revision: Union[str, None] = "f8a9b0c1d2e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "price_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("price_nzd", sa.Float, nullable=False),
        sa.Column("promo_price_nzd", sa.Float, nullable=True),
        sa.Column("is_member_only", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_price_history_product_recorded", "price_history", ["product_id", "recorded_at"])
    op.create_index("ix_price_history_recorded_at", "price_history", ["recorded_at"])


def downgrade() -> None:
    op.drop_index("ix_price_history_recorded_at", table_name="price_history")
    op.drop_index("ix_price_history_product_recorded", table_name="price_history")
    op.drop_table("price_history")
