"""Audit current database coverage and generate report."""
import asyncio
from app.db.session import get_async_session
from app.db.models import Store
from sqlalchemy import select, func

# Expected counts for all chains
EXPECTED_COUNTS = {
    "New World": 150,
    "PAK'nSAVE": 61,
    "Liquorland": 170,
    "Super Liquor": 140,
    "Bottle O": 114,
    "Thirsty Liquor": 106,
    "Black Bull": 59,
    "Big Barrel": 51,
    "Glengarry": 18,
    "Liquor Centre": 240,
}

async def audit_coverage():
    """Audit current coverage in database."""
    print("=" * 80)
    print("DATABASE COVERAGE AUDIT")
    print("=" * 80)
    print()

    async with get_async_session() as session:
        # Get actual counts from database
        result = await session.execute(
            select(Store.chain, func.count(Store.id))
            .group_by(Store.chain)
            .order_by(Store.chain)
        )

        actual_counts = dict(result.all())

    # Calculate coverage for each chain
    print(f"{'Chain':<20} {'We Have':<10} {'Expected':<10} {'Coverage':<10} {'Status'}")
    print("-" * 80)

    total_actual = 0
    total_expected = 0
    needs_work = []

    for chain in sorted(EXPECTED_COUNTS.keys()):
        expected = EXPECTED_COUNTS[chain]
        actual = actual_counts.get(chain, 0)
        coverage = (actual / expected * 100) if expected > 0 else 0

        total_actual += actual
        total_expected += expected

        # Status indicator
        if coverage >= 90:
            status = "✅ Complete"
        elif coverage >= 50:
            status = "🟡 Partial"
        elif coverage > 0:
            status = "🟠 Started"
        else:
            status = "❌ Missing"
            needs_work.append(chain)

        print(f"{chain:<20} {actual:<10} {expected:<10} {coverage:>7.1f}%   {status}")

    print("-" * 80)
    overall_coverage = (total_actual / total_expected * 100)
    print(f"{'TOTAL':<20} {total_actual:<10} {total_expected:<10} {overall_coverage:>7.1f}%")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"✅ Chains completed (≥90%):  {sum(1 for c in EXPECTED_COUNTS if (actual_counts.get(c, 0) / EXPECTED_COUNTS[c] * 100) >= 90)}")
    print(f"🟡 Chains partial (50-89%):   {sum(1 for c in EXPECTED_COUNTS if 50 <= (actual_counts.get(c, 0) / EXPECTED_COUNTS[c] * 100) < 90)}")
    print(f"🟠 Chains started (1-49%):    {sum(1 for c in EXPECTED_COUNTS if 0 < (actual_counts.get(c, 0) / EXPECTED_COUNTS[c] * 100) < 50)}")
    print(f"❌ Chains missing (0%):       {len(needs_work)}")
    print()

    if needs_work:
        print("Chains needing work:")
        for chain in needs_work:
            expected = EXPECTED_COUNTS[chain]
            needed = int(expected * 0.9)  # 90% target
            print(f"  - {chain}: Need {needed} stores (0/{expected} currently)")

    print()
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print()
    print("Run: python scripts/analyze_chain_roi.py")
    print("To see prioritized list by ROI")

if __name__ == "__main__":
    asyncio.run(audit_coverage())
