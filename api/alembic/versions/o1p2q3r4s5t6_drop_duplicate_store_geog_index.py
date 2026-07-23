"""Drop the duplicate GeoAlchemy-generated store geography index.

Revision ID: o1p2q3r4s5t6
Revises: n1o2p3q4r5s6
Create Date: 2026-07-23
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "o1p2q3r4s5t6"
down_revision: Union[str, Sequence[str], None] = "n1o2p3q4r5s6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The original PostGIS migration created ix_stores_geog explicitly while
    # GeoAlchemy also created idx_stores_geog via its DDL event.
    op.execute("DROP INDEX IF EXISTS public.idx_stores_geog")


def downgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_stores_geog
        ON public.stores
        USING gist (geog)
        """
    )
