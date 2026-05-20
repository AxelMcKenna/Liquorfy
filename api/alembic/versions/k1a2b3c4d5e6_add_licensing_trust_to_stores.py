"""Add sells_alcohol + licensing_trust_area to stores, backfill via classifier.

Implements the West Auckland Trust monopoly rule: supermarkets and non-Trust
off-licences inside the Portage / Waitakere Licensing Trust districts cannot
legally sell alcohol under the Sale and Supply of Alcohol Act 2012.

Revision ID: k1a2b3c4d5e6
Revises: h2c3d4e5f6g7
Create Date: 2026-05-20
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "k1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "h2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Schema.
    op.add_column(
        "stores",
        sa.Column(
            "sells_alcohol",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "stores",
        sa.Column("licensing_trust_area", sa.String(length=32), nullable=True),
    )

    # 2. Backfill via the classifier. We import here, not at module top, because
    # alembic's autogenerate / offline-mode scripts shouldn't pay the import
    # cost when only generating SQL.
    from app.services.licensing_trusts import classify_store

    bind = op.get_bind()
    stores = sa.table(
        "stores",
        sa.column("id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.column("chain", sa.String()),
        sa.column("name", sa.String()),
        sa.column("api_id", sa.String()),
        sa.column("lat", sa.Float()),
        sa.column("lon", sa.Float()),
        sa.column("sells_alcohol", sa.Boolean()),
        sa.column("licensing_trust_area", sa.String()),
    )

    rows = bind.execute(
        sa.select(stores.c.id, stores.c.chain, stores.c.name, stores.c.api_id, stores.c.lat, stores.c.lon)
    ).fetchall()

    for store_id, chain, name, api_id, lat, lon in rows:
        result = classify_store(chain=chain, name=name, api_id=api_id, lat=lat, lon=lon)
        if not result.sells_alcohol or result.licensing_trust_area is not None:
            bind.execute(
                sa.update(stores)
                .where(stores.c.id == store_id)
                .values(
                    sells_alcohol=result.sells_alcohol,
                    licensing_trust_area=result.licensing_trust_area,
                )
            )

    op.create_index(
        "ix_store_sells_alcohol",
        "stores",
        ["sells_alcohol"],
        postgresql_where=sa.text("sells_alcohol = false"),
    )


def downgrade() -> None:
    op.drop_index("ix_store_sells_alcohol", table_name="stores")
    op.drop_column("stores", "licensing_trust_area")
    op.drop_column("stores", "sells_alcohol")
