import asyncio
import asyncpg
import os

async def run():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    rows = await conn.fetch("""
        SELECT pid, state, query, now() - query_start AS duration
        FROM pg_stat_activity
        WHERE state <> 'idle'
        ORDER BY duration DESC NULLS LAST
        LIMIT 20
    """)
    for r in rows:
        print(f"PID={r['pid']} state={r['state']} duration={r['duration']} query={r['query'][:120]}")
    if not rows:
        print("No active queries")
    await conn.close()

asyncio.run(run())
