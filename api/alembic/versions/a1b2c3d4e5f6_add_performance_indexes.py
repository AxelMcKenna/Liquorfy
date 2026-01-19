"""Add performance indexes

Revision ID: a1b2c3d4e5f6
Revises: 7f1535a4ebaa
Create Date: 2026-01-19

This migration adds critical indexes for production performance:
- Foreign key indexes on prices table (product_id, store_id)
- Composite index for product-store lookups
- Chain column indexes for filtering
- Ingestion run indexes for status queries
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '7f1535a4ebaa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes."""
    # Critical: Foreign key indexes on prices table
    op.create_index("ix_price_product_id", "prices", ["product_id"])
    op.create_index("ix_price_store_id", "prices", ["store_id"])

    # Critical: Composite index for product-store lookups (used in JOINs and batch operations)
    op.create_index("ix_price_product_store", "prices", ["product_id", "store_id"])

    # Critical: Chain column indexes for filtering
    op.create_index("ix_store_chain", "stores", ["chain"])
    op.create_index("ix_product_chain", "products", ["chain"])

    # High: Ingestion run indexes for status and recent run queries
    op.create_index("ix_ingestion_run_chain_status", "ingestion_runs", ["chain", "status"])
    op.create_index("ix_ingestion_run_chain_started", "ingestion_runs", ["chain", "started_at"])

    # Medium: Index on last_seen_at for cleanup queries
    op.create_index("ix_price_last_seen", "prices", ["last_seen_at"])


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index("ix_price_product_id", table_name="prices")
    op.drop_index("ix_price_store_id", table_name="prices")
    op.drop_index("ix_price_product_store", table_name="prices")
    op.drop_index("ix_store_chain", table_name="stores")
    op.drop_index("ix_product_chain", table_name="products")
    op.drop_index("ix_ingestion_run_chain_status", table_name="ingestion_runs")
    op.drop_index("ix_ingestion_run_chain_started", table_name="ingestion_runs")
    op.drop_index("ix_price_last_seen", table_name="prices")
