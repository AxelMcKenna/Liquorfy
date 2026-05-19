"""Clean up corrupted Countdown product names.

Historical context: the Countdown scraper concatenated
`brand + variety + name` into `products.name`, but the Woolworths API's
`name` field already contains the brand+variety prefix. This produced
strings like:

  "kim crawford  kim crawford chardonnay 750mL"
  "speights summit lime speights summit beer lager lime 12x330mL"

The simple double-space form is safe to fix with a regex. The complex
multi-field form is NOT regex-safe and should be repaired by re-running
the scraper (the next scrape upserts on (chain, source_product_id) and
overwrites `name` with the now-clean string).

Usage:
    cd api && python scripts/maintenance/cleanup_countdown_names.py [--dry-run]

The script is idempotent — re-running it is a no-op once names are clean.
After running, re-run `scripts/backfill_canonical_ids.py` so that the
repaired products get canonical IDs that match the other chains.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy import text

from app.db.session import async_transaction, get_async_session


# Matches "<X>  <X> ..." — a token-or-phrase followed by 2+ spaces and the
# same phrase again followed by at least one more space. Anchored to the
# start of the string so we only collapse the leading duplicate prefix
# and never touch substrings in the middle of a name.
DOUBLESPACE_DUP_PATTERN = r"^(.+?)\s{2,}\1\s+"


async def count_corrupted() -> tuple[int, int]:
    """Return (double_space_corrupted, total_countdown)."""
    async with get_async_session() as session:
        result = await session.execute(
            text(
                """
                SELECT
                    COUNT(*) FILTER (WHERE name ~ :pattern) AS corrupted,
                    COUNT(*) AS total
                FROM products
                WHERE chain = 'countdown'
                """
            ),
            {"pattern": DOUBLESPACE_DUP_PATTERN},
        )
        row = result.one()
        return int(row.corrupted), int(row.total)


async def sample_corrupted(limit: int = 5) -> list[tuple[str, str]]:
    """Return (before, after) preview for a few corrupted rows."""
    async with get_async_session() as session:
        result = await session.execute(
            text(
                """
                SELECT name AS before,
                       regexp_replace(name, :pattern, '\\1 ') AS after
                FROM products
                WHERE chain = 'countdown' AND name ~ :pattern
                ORDER BY name
                LIMIT :limit
                """
            ),
            {"pattern": DOUBLESPACE_DUP_PATTERN, "limit": limit},
        )
        return [(row.before, row.after) for row in result.all()]


async def apply_fix() -> int:
    """Rewrite the duplicated-prefix names. Returns row count updated."""
    async with async_transaction() as session:
        result = await session.execute(
            text(
                """
                UPDATE products
                SET name = regexp_replace(name, :pattern, '\\1 ')
                WHERE chain = 'countdown'
                  AND name ~ :pattern
                """
            ),
            {"pattern": DOUBLESPACE_DUP_PATTERN},
        )
        return result.rowcount or 0


async def main(dry_run: bool) -> None:
    corrupted, total = await count_corrupted()
    print(f"Countdown rows total:               {total:,}")
    print(f"Rows matching double-space pattern: {corrupted:,}")

    if corrupted == 0:
        print("Nothing to fix.")
        return

    print("\nSample fixes:")
    for before, after in await sample_corrupted():
        print(f"  - {before!r}")
        print(f"    → {after!r}")

    if dry_run:
        print("\n--dry-run: no rows modified.")
        return

    print()
    fixed = await apply_fix()
    print(f"Updated {fixed:,} rows.")
    print(
        "\nNext steps:\n"
        "  1. Re-scrape Countdown to fix any complex-pattern names not\n"
        "     covered by this regex (they will be overwritten on upsert).\n"
        "  2. Re-run scripts/backfill_canonical_ids.py so the cleaned\n"
        "     products get canonical IDs that align with other chains."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing.",
    )
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
