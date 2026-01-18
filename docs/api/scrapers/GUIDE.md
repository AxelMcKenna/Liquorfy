# Liquorfy Scraper Guide

Complete guide to running product scrapers to populate the Liquorfy database with fresh pricing data.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Available Scrapers](#available-scrapers)
4. [Quick Start](#quick-start)
5. [Detailed Usage](#detailed-usage)
6. [Understanding Output](#understanding-output)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Overview

Liquorfy uses automated scrapers to collect product and pricing data from 8 major New Zealand liquor retailers. Each scraper:

- Fetches product catalog pages (live scraping or browser automation)
- Parses product details (name, price, promotions, images, etc.)
- Upserts products into the database
- Creates/updates price records for each store
- Tracks changes and generates ingestion run reports

**Data Flow:**
```
Website → Scraper → Product Parser → Database
                         ↓
                  Promotion Detection
                  (via promo_utils)
```

---

## Prerequisites

### 1. Database Setup

Ensure PostgreSQL is running:

```bash
# Check if postgres container is running
docker ps | grep postgres

# If not running, start it
cd /Users/axelmckenna/Liquorfy
docker-compose up -d postgres
```

### 2. Python Environment

```bash
cd /Users/axelmckenna/Liquorfy/api

# Install dependencies
poetry install

# For browser-based scrapers (New World, PakNSave, Countdown, Glengarry)
poetry run playwright install
```

### 3. Environment Variables

Check your `.env` file contains:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/liquorfy
ENVIRONMENT=development
```

---

## Available Scrapers

| Chain | Type | Products | Notes |
|-------|------|----------|-------|
| **super_liquor** | HTTP | ~500 | Fast, reliable |
| **liquorland** | HTTP | ~1,200 | Fast, reliable |
| **liquor_centre** | HTTP | ~800 | Fast, reliable |
| **bottle_o** | HTTP | ~450 | Fast, reliable |
| **new_world** | Browser | ~1,800 | Slower (Playwright) |
| **paknsave** | Browser | ~1,600 | Slower (Playwright) |
| **countdown** | Browser | ~250 | Slower (Playwright) |
| **glengarry** | Browser | ~650 | Slower (Playwright) |

**Total:** ~7,250 unique products across all chains

---

## Quick Start

### Option A: Run Everything (Recommended for Fresh Setup)

```bash
cd /Users/axelmckenna/Liquorfy/api

# 1. Clear old price data (optional, recommended for clean slate)
poetry run python scripts/clear_price_data.py --confirm

# 2. Test one scraper first
poetry run python scripts/run_single_scraper.py super_liquor

# 3. If test passes, run all scrapers
poetry run python scripts/run_all_scrapers.py --confirm
```

### Option B: Run Individual Scraper

```bash
cd /Users/axelmckenna/Liquorfy/api

# Run a specific chain
poetry run python scripts/run_single_scraper.py <chain_name>

# Examples:
poetry run python scripts/run_single_scraper.py super_liquor
poetry run python scripts/run_single_scraper.py liquorland
poetry run python scripts/run_single_scraper.py new_world
```

---

## Detailed Usage

### 1. Clear Old Price Data

**Purpose:** Remove stale price records before a fresh scrape.

**What it keeps:**
- ✅ Products (product metadata)
- ✅ Stores (store locations)
- ✅ Ingestion Runs (scrape history)

**What it deletes:**
- ❌ All Price records

**Usage:**

```bash
# Dry run (preview only, no changes)
poetry run python scripts/clear_price_data.py

# Actually delete data
poetry run python scripts/clear_price_data.py --confirm
```

**Example Output:**
```
============================================================
DATABASE CLEANUP - CURRENT STATE
============================================================
📦 Products:  7,234 (will be KEPT)
🏪 Stores:    156 (will be KEPT)
💰 Prices:    52,847 (will be DELETED)
============================================================

Are you sure you want to continue? Type 'yes' to confirm: yes

🗑️  Deleting price records...
============================================================
✅ CLEANUP COMPLETE
============================================================
Deleted:   52,847 price records
Remaining: 0 prices
Products:  7,234 (unchanged)
Stores:    156 (unchanged)
============================================================

✨ Database is ready for fresh scraping!
```

### 2. Run Single Scraper

**Purpose:** Test a single chain or update specific retailer data.

**Usage:**

```bash
poetry run python scripts/run_single_scraper.py <chain>

# Available chains:
poetry run python scripts/run_single_scraper.py super_liquor
poetry run python scripts/run_single_scraper.py liquorland
poetry run python scripts/run_single_scraper.py liquor_centre
poetry run python scripts/run_single_scraper.py bottle_o
poetry run python scripts/run_single_scraper.py new_world
poetry run python scripts/run_single_scraper.py paknsave
poetry run python scripts/run_single_scraper.py countdown
poetry run python scripts/run_single_scraper.py glengarry
```

**Example Output:**
```
🚀 Running super_liquor scraper...
   Class: SuperLiquorScraper

============================================================
✅ SCRAPER COMPLETED SUCCESSFULLY
============================================================
Status:        completed
Total items:   523
Changed items: 523
Failed items:  0
Started:       2025-12-26 15:43:26.061500+00:00
Finished:      2025-12-26 15:45:12.140928
Duration:      0:01:46.079428
============================================================
```

### 3. Run All Scrapers

**Purpose:** Populate database with comprehensive pricing data from all retailers.

**Usage:**

```bash
# Dry run (preview execution plan)
poetry run python scripts/run_all_scrapers.py

# Actually run all scrapers
poetry run python scripts/run_all_scrapers.py --confirm
```

**Execution Flow:**
1. Shows execution plan (8 chains)
2. Prompts for confirmation
3. Runs scrapers sequentially
4. Shows progress for each chain
5. Handles errors gracefully (prompts to continue)
6. Provides comprehensive summary

**Example Output:**
```
======================================================================
SCRAPER EXECUTION PLAN
======================================================================
Total scrapers: 8
Chains to scrape:
  1. super_liquor
  2. liquorland
  3. liquor_centre
  4. bottle_o
  5. new_world
  6. paknsave
  7. countdown
  8. glengarry
======================================================================

⚠️  This will scrape all chains and update the database!
⚠️  This may take 30-60 minutes depending on rate limits.

Are you sure you want to continue? Type 'yes' to confirm: yes

🚀 Starting scraper execution...

======================================================================
[1/8] Running super_liquor scraper...
======================================================================

✅ super_liquor completed successfully!
   Status: completed
   Total items: 523
   Changed items: 523
   Failed items: 0
   Duration: 0:01:46.079428

... (continues for all 8 chains)

======================================================================
SCRAPING COMPLETE - FINAL SUMMARY
======================================================================
Total duration: 0:45:23.123456
Successful: 8/8
Failed: 0/8

✅ Successful scrapers:
   • super_liquor: 523 products, 523 changed
   • liquorland: 1,247 products, 1,247 changed
   • liquor_centre: 892 products, 892 changed
   • bottle_o: 456 products, 456 changed
   • new_world: 1,834 products, 1,834 changed
   • paknsave: 1,612 products, 1,612 changed
   • countdown: 234 products, 234 changed
   • glengarry: 678 products, 678 changed
   TOTAL: 7,476 products, 7,476 price updates
======================================================================

🎉 All done! Database has been updated with fresh pricing data.
```

---

## Understanding Output

### Scraper Metrics

Each scraper reports these metrics:

| Metric | Description |
|--------|-------------|
| **Total items** | Total number of products processed |
| **Changed items** | Products with price/data changes |
| **Failed items** | Products that failed to process |
| **Duration** | Time taken to complete scrape |

### Database Records

After scraping, the database contains:

**Products Table:**
- One record per unique product (identified by `chain` + `source_product_id`)
- Contains: name, brand, category, ABV, volume, images, etc.

**Prices Table:**
- One record per product × store combination
- Contains: current price, promo price, promo text, member-only flag
- Tracks: `last_seen_at`, `price_last_changed_at`

**Stores Table:**
- Pre-populated with retailer store locations
- Each store belongs to a chain

**Ingestion Runs Table:**
- Historical log of all scraper executions
- Tracks success/failure, item counts, timestamps

### Promotion Detection

The scraper automatically detects and extracts promotions using `promo_utils.py`:

**Detected Patterns:**
- "2 for $X" → `promo_price_nzd`, `promo_text`
- "Save $X" → Calculated promo price
- "Members only" → `is_member_only = true`
- "Free glass with purchase" → `promo_text`
- Date ranges → `promo_ends_at`

**Example:**
```python
# Input
raw_price = "$49.99"
promo_text = "2 for $80 - Members Only - Ends 31/12/2025"

# Output
price_nzd = 49.99
promo_price_nzd = 40.00  # $80 / 2
promo_text = "2 for $80"
is_member_only = True
promo_ends_at = datetime(2025, 12, 31)
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Error

**Error:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution:**
```bash
# Check postgres is running
docker ps | grep postgres

# Start postgres
docker-compose up -d postgres

# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL
```

#### 2. Browser Playwright Not Installed

**Error:**
```
playwright._impl._api_types.Error: Executable doesn't exist
```

**Solution:**
```bash
# Install playwright browsers
poetry run playwright install

# Or install specific browser
poetry run playwright install chromium
```

#### 3. High Failed Items Count

**Possible Causes:**
- Website structure changed (scraper needs update)
- Rate limiting / IP blocking
- Network issues

**Solution:**
```bash
# Check logs for specific errors
poetry run python scripts/run_single_scraper.py <chain> 2>&1 | tee scraper.log

# Review error patterns
grep "ERROR" scraper.log | head -20
```

#### 4. Timezone / Datetime Errors

**Error:**
```
TypeError: can't subtract offset-naive and offset-aware datetimes
```

**Solution:**
This has been fixed in `scripts/run_single_scraper.py`. Make sure you're using the latest version.

#### 5. Slow Performance

**Causes:**
- Browser-based scrapers are inherently slower
- Rate limits from websites
- Large number of products

**Solutions:**
- Run HTTP-based scrapers first (faster)
- Schedule during off-peak hours
- Use `run_single_scraper.py` for targeted updates

---

## Best Practices

### 1. Regular Scraping Schedule

**Recommended:**
- **Daily:** Run all scrapers to keep prices fresh
- **Weekly:** Clear old price data and re-scrape
- **On-Demand:** Run single scraper when specific chain needs update

**Cron Example:**
```bash
# Daily scrape at 2 AM
0 2 * * * cd /Users/axelmckenna/Liquorfy/api && poetry run python scripts/run_all_scrapers.py --confirm

# Weekly cleanup on Sunday at 1 AM
0 1 * * 0 cd /Users/axelmckenna/Liquorfy/api && poetry run python scripts/clear_price_data.py --confirm
```

### 2. Testing Before Production

Always test a single scraper before running all:

```bash
# Test fastest scraper first
poetry run python scripts/run_single_scraper.py super_liquor

# If successful, run all
poetry run python scripts/run_all_scrapers.py --confirm
```

### 3. Monitoring

Track scraper health:

```bash
# Check latest ingestion runs
psql $DATABASE_URL -c "
SELECT chain, status, items_total, items_changed, items_failed, started_at
FROM ingestion_runs
ORDER BY started_at DESC
LIMIT 10;
"

# Check price freshness
psql $DATABASE_URL -c "
SELECT chain, COUNT(*), MAX(last_seen_at) as latest_update
FROM prices p
JOIN products pr ON p.product_id = pr.id
GROUP BY chain
ORDER BY chain;
"
```

### 4. Error Handling

The `run_all_scrapers.py` script has built-in error handling:
- If a scraper fails, you'll be prompted to continue or abort
- Failed scrapers are reported in the final summary
- Successful scrapers are not re-run if you abort and restart

### 5. Database Backups

Before major scraping operations:

```bash
# Backup database
docker exec infra-db-1 pg_dump -U postgres liquorfy > backup_$(date +%Y%m%d).sql

# Restore if needed
cat backup_20251226.sql | docker exec -i infra-db-1 psql -U postgres liquorfy
```

---

## Advanced Usage

### Custom Scraper Development

To add a new scraper:

1. Create scraper class in `app/scrapers/`
2. Extend `Scraper` base class
3. Implement `fetch_catalog_pages()` and `parse_products()`
4. Register in `app/scrapers/registry.py`

See existing scrapers for examples:
- `super_liquor.py` - Simple HTTP scraper
- `new_world.py` - Browser-based scraper
- `liquor_centre.py` - HTML parsing with fixtures

### Fixture-Based Development

For testing scrapers without hitting live websites:

```python
# Save HTML fixture
curl "https://website.com/products" > api/app/scrapers/fixtures/chain_live.html

# Use fixture in scraper
scraper = SuperLiquorScraper(use_fixtures=True)
```

### Database Queries

Useful queries for analyzing scraped data:

```sql
-- Products with promotions
SELECT name, chain, promo_text, promo_price_nzd
FROM products p
JOIN prices pr ON p.id = pr.product_id
WHERE pr.promo_price_nzd IS NOT NULL
ORDER BY (p.price_nzd - pr.promo_price_nzd) DESC
LIMIT 20;

-- Price distribution by chain
SELECT
    chain,
    COUNT(*) as product_count,
    AVG(price_nzd) as avg_price,
    MIN(price_nzd) as min_price,
    MAX(price_nzd) as max_price
FROM products p
GROUP BY chain
ORDER BY avg_price DESC;

-- Member-only deals
SELECT chain, COUNT(*) as member_deals
FROM prices
WHERE is_member_only = true
GROUP BY chain;
```

---

## Summary

You now have everything needed to run Liquorfy scrapers:

**Quick Commands:**
```bash
# Full refresh workflow
cd /Users/axelmckenna/Liquorfy/api
poetry run python scripts/clear_price_data.py --confirm
poetry run python scripts/run_all_scrapers.py --confirm

# Test single scraper
poetry run python scripts/run_single_scraper.py super_liquor

# Check results
psql $DATABASE_URL -c "SELECT chain, COUNT(*) FROM products GROUP BY chain;"
```

**Need Help?**
- Check the [DB_SCHEMA.md](DB_SCHEMA.md) for database structure
- Review scraper source code in `api/app/scrapers/`
- Check promotion parsing in `api/app/services/promo_utils.py`

Happy scraping! 🚀🍺
