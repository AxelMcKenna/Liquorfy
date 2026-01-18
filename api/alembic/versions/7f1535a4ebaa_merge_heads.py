"""merge heads

Revision ID: 7f1535a4ebaa
Revises: 2d2e5caa1f3b, 1423fd809e0b
Create Date: 2026-01-02 08:13:38.558573

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f1535a4ebaa'
down_revision: Union[str, Sequence[str], None] = ('2d2e5caa1f3b', '1423fd809e0b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
