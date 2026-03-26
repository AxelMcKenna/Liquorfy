import asyncio
import asyncpg
import os

async def run():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])

    # Kill the stale idle-in-transaction session
    result = await conn.fetch("""
        SELECT pid, pg_terminate_backend(pid) as terminated
        FROM pg_stat_activity
        WHERE state = 'idle in transaction'
          AND now() - query_start > interval '1 hour'
    """)
    for r in result:
        print(f"Terminated PID {r['pid']}: {r['terminated']}")
    if not result:
        print("No stale transactions found")
    await conn.close()

asyncio.run(run())
