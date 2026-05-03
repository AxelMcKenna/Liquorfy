"""Merge price_history and product_views heads.

Revision ID: h1a2b3c4d5e6
Revises: a1b2c3d4e5f7, g1a2b3c4d5e6
Create Date: 2026-05-04
"""
from typing import Sequence, Union


revision: str = "h1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = ("a1b2c3d4e5f7", "g1a2b3c4d5e6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
