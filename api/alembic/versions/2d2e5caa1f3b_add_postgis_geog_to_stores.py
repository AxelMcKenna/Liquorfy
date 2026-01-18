"""add_postgis_geog_to_stores

Revision ID: 2d2e5caa1f3b
Revises: d05d160f7b38
Create Date: 2025-01-05 10:15:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography


# revision identifiers, used by Alembic.
revision: str = "2d2e5caa1f3b"
down_revision: Union[str, Sequence[str], None] = "d05d160f7b38"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.alter_column("stores", "lat", nullable=True)
    op.alter_column("stores", "lon", nullable=True)
    op.add_column(
        "stores",
        sa.Column(
            "geog",
            Geography(geometry_type="POINT", srid=4326),
            sa.Computed(
                "CASE WHEN lat IS NULL OR lon IS NULL THEN NULL "
                "ELSE ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography END",
                persisted=True,
            ),
            nullable=True,
        ),
    )
    op.create_index("ix_stores_geog", "stores", ["geog"], postgresql_using="gist")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_stores_geog", table_name="stores")
    op.drop_column("stores", "geog")
    op.alter_column("stores", "lon", nullable=False)
    op.alter_column("stores", "lat", nullable=False)
    op.execute("DROP EXTENSION IF EXISTS postgis")
