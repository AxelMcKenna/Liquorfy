"""Prefix Woolworths to countdown store names.

Existing countdown stores were ingested without the chain display-name
prefix (e.g. "Eastgate" instead of "Woolworths Eastgate").  This
migration normalises them so the store-location scraper's
``ON CONFLICT (chain, name)`` upsert matches correctly on future runs.

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-02-25 20:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, Sequence[str], None] = "d6e7f8a9b0c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Strip trailing " Woolworths" suffix
    # (CDX API returns "Eastgate Woolworths"; runner.py strips this then
    # prepends, so the canonical form is "Woolworths Eastgate".)
    op.execute(
        """
        UPDATE stores
        SET name = TRIM(LEFT(name, LENGTH(name) - LENGTH(' Woolworths')))
        WHERE chain = 'countdown'
          AND name ILIKE '%% Woolworths'
          AND name NOT ILIKE 'Woolworths %%'
        """
    )

    # Step 2: Prepend "Woolworths " to any countdown store that doesn't
    # already have the prefix (covers both bare names and newly-trimmed ones).
    op.execute(
        """
        UPDATE stores
        SET name = 'Woolworths ' || name
        WHERE chain = 'countdown'
          AND name NOT ILIKE 'Woolworths %%'
          AND name NOT ILIKE 'Metro %%'
        """
    )


def downgrade() -> None:
    # Remove the "Woolworths " prefix we added.
    op.execute(
        """
        UPDATE stores
        SET name = TRIM(SUBSTRING(name FROM 13))
        WHERE chain = 'countdown'
          AND name ILIKE 'Woolworths %%'
        """
    )
