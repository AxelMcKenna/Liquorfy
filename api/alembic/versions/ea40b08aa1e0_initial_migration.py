"""Initial migration

Revision ID: ea40b08aa1e0
Revises: 
Create Date: 2025-12-20 18:14:09.565067

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea40b08aa1e0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create stores table
    op.create_table(
        'stores',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('chain', sa.String(length=64), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lon', sa.Float(), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('region', sa.String(length=64), nullable=True),
        sa.Column('url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chain', sa.String(length=64), nullable=False),
        sa.Column('source_product_id', sa.String(length=128), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('brand', sa.String(length=128), nullable=True),
        sa.Column('category', sa.String(length=64), nullable=True),
        sa.Column('abv_percent', sa.Float(), nullable=True),
        sa.Column('pack_count', sa.Integer(), nullable=True),
        sa.Column('unit_volume_ml', sa.Float(), nullable=True),
        sa.Column('total_volume_ml', sa.Float(), nullable=True),
        sa.Column('image_url', sa.String(length=255), nullable=True),
        sa.Column('product_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chain', 'source_product_id', name='uq_product_source')
    )

    # Create ingestion_runs table
    op.create_table(
        'ingestion_runs',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chain', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('items_total', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('items_changed', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('items_failed', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('log_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create prices table with foreign keys
    op.create_table(
        'prices',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('store_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True, server_default='NZD'),
        sa.Column('price_nzd', sa.Float(), nullable=False),
        sa.Column('promo_price_nzd', sa.Float(), nullable=True),
        sa.Column('promo_text', sa.String(length=255), nullable=True),
        sa.Column('promo_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('price_last_changed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_member_only', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for prices table
    op.create_index('ix_price_price_nzd', 'prices', ['price_nzd'])
    op.create_index('ix_price_promo_price_nzd', 'prices', ['promo_price_nzd'])
    op.create_index('ix_price_last_changed', 'prices', ['price_last_changed_at'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.drop_index('ix_price_last_changed', table_name='prices')
    op.drop_index('ix_price_promo_price_nzd', table_name='prices')
    op.drop_index('ix_price_price_nzd', table_name='prices')

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('prices')
    op.drop_table('ingestion_runs')
    op.drop_table('products')
    op.drop_table('stores')
