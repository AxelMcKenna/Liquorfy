"""Check recent ingestion runs."""
import asyncio
from sqlalchemy import select
from app.db.session import async_transaction
from app.db.models import IngestionRun


async def main():
    async with async_transaction() as session:
        # Get most recent runs
        result = await session.execute(
            select(IngestionRun)
            .order_by(IngestionRun.started_at.desc())
            .limit(10)
        )
        runs = result.scalars().all()

        print("=" * 80)
        print("MOST RECENT INGESTION RUNS")
        print("=" * 80)

        for run in runs:
            duration = ""
            if run.finished_at and run.started_at:
                duration_sec = (run.finished_at - run.started_at).total_seconds()
                duration = f"{duration_sec:.1f}s"
            elif run.started_at:
                from datetime import datetime
                duration_sec = (datetime.utcnow() - run.started_at).total_seconds()
                duration = f"Running for {duration_sec:.1f}s"

            print(f"\n{run.chain:20s} | {run.status:10s}")
            print(f"  Started:  {run.started_at}")
            print(f"  Finished: {run.finished_at}")
            print(f"  Duration: {duration}")
            print(f"  Items:    {run.items_total or 0} total, {run.items_changed or 0} changed, {run.items_failed or 0} failed")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
