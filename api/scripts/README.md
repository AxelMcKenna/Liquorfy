# Scripts Directory

Utility and maintenance scripts for the Liquorfy application.

## Directory Structure

```
scripts/
├── utilities/          # Database analysis and reporting tools
├── maintenance/        # Data cleanup and backfill operations
└── README.md          # This file
```

---

## Utilities

### `analyze_db_state.py`
Comprehensive database analysis tool.

**Usage:**
```bash
poetry run python scripts/utilities/analyze_db_state.py
```

**Output:**
- Products breakdown by chain
- Store counts per chain
- Price records per chain
- Full database schema with columns, constraints, and indexes
- Top categories per chain

**Use Cases:**
- Database health check
- Understanding data distribution
- Schema documentation
- Performance index verification

---

### `check_liquor_centre_summary.py`
Quick summary of Liquor Centre scraping results.

**Usage:**
```bash
poetry run python scripts/utilities/check_liquor_centre_summary.py
```

**Output:**
- Total products, stores, and prices
- Category distribution (top 15)
- Sample categorized products
- Category coverage percentage

**Use Cases:**
- Quick status check after scraping
- Verify category inference is working
- Monitor data quality

---

## Maintenance

### `backfill_categories.py`
Re-run category inference on products with NULL categories.

**Usage:**
```bash
poetry run python scripts/maintenance/backfill_categories.py
```

**What it does:**
- Finds all products with `category: None`
- Runs the `infer_category()` function on each
- Updates the database with inferred categories
- Reports statistics

**When to use:**
- After improving category inference keywords/mappings
- After adding new brand mappings
- To fix products that were previously uncategorized

**Output:**
```
✅ Updated: 315 products
❌ Still NULL: 1,099 products
📊 Category Distribution (Top 15)
```

---

### `cleanup_duplicate_stores.py`
Remove duplicate store records from the database.

**Usage:**
```bash
poetry run python scripts/maintenance/cleanup_duplicate_stores.py
```

**What it does:**
1. Identifies duplicate stores by `(chain, url)`
2. Updates all `prices` to point to the canonical (oldest) store
3. Deletes duplicate store records
4. Adds unique constraint to prevent future duplicates

**When to use:**
- After discovering duplicate stores in the database
- One-time cleanup (constraint prevents future duplicates)
- **Already run successfully** - not needed unless duplicates reappear

**Safety:**
- Preserves all price data
- Updates foreign keys before deletion
- Atomic transaction (all or nothing)

---

## Running Scripts

All scripts should be run from the `api/` directory using Poetry:

```bash
# From api/ directory
cd /path/to/Liquorfy/api

# Run a utility script
poetry run python scripts/utilities/analyze_db_state.py

# Run a maintenance script
poetry run python scripts/maintenance/backfill_categories.py
```

---

## Database Connection

All scripts use the same database connection string:
```
postgresql+asyncpg://postgres:postgres@localhost:5432/liquorfy
```

Ensure your PostgreSQL database is running before executing scripts.

---

## Adding New Scripts

When adding new scripts:

1. **Utilities** - Read-only analysis/reporting tools → `scripts/utilities/`
2. **Maintenance** - Data modification/cleanup tools → `scripts/maintenance/`
3. Add documentation to this README
4. Include usage examples and expected output
5. Use async/await with SQLAlchemy AsyncEngine
6. Include proper logging and error handling

### Template:

```python
"""
Script description
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine(
        'postgresql+asyncpg://postgres:postgres@localhost:5432/liquorfy'
    )

    async with engine.begin() as conn:
        # Your code here
        pass

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Archived Scripts

Older debug and test scripts have been moved to `archived/` directory.
These can be safely deleted once you're comfortable the cleanup was successful.

Review and delete:
```bash
rm -rf archived/
```
