"""Generate final store summary with expected vs actual counts."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, func
from app.db.models import Store
from app.db.session import async_transaction


# Expected counts based on research
EXPECTED_COUNTS = {
    "New World": 150,
    "PAK'nSAVE": 61,
    "Liquorland": 170,
    "Super Liquor": 140,
    "Glengarry": 18,
    "Bottle O": 114,
    "Liquor Centre": 240,
    "Thirsty Liquor": 106,
    "Black Bull": 59,
    "Big Barrel": 51,
    # Countdown excluded per user request
}


async def main():
    """Generate summary."""
    async with async_transaction() as session:
        result = await session.execute(
            select(Store.chain, func.count()).group_by(Store.chain).order_by(Store.chain)
        )
        actual_counts = dict(result.all())

    print("\n" + "="*80)
    print("FINAL STORE LOCATION SUMMARY")
    print("="*80)
    print(f"\n{'Store Chain':<20} {'We Have':<10} {'Expected':<10} {'Coverage':<10} {'Status':<10}")
    print("-" * 80)

    total_have = 0
    total_expected = 0

    for chain, expected in sorted(EXPECTED_COUNTS.items(), key=lambda x: x[1], reverse=True):
        have = actual_counts.get(chain, 0)
        total_have += have
        total_expected += expected

        coverage = f"{(have/expected*100):.0f}%" if expected > 0 else "N/A"

        if have >= expected * 0.9:  # 90%+ coverage
            status = "✅"
        elif have >= expected * 0.5:  # 50%+ coverage
            status = "⚠️ "
        else:
            status = "❌"

        print(f"{status} {chain:<18} {have:<10} {expected:<10} {coverage:<10}")

    print("-" * 80)
    overall_coverage = f"{(total_have/total_expected*100):.1f}%"
    print(f"{'TOTAL':<20} {total_have:<10} {total_expected:<10} {overall_coverage:<10}")
    print("\n" + "="*80)
    print(f"Overall Coverage: {overall_coverage}")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
