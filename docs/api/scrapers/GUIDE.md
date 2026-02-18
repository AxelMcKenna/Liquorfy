# Liquorfy Scraper Guide

Complete guide to running product scrapers to populate the Liquorfy database with fresh pricing data.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Available Scrapers](#available-scrapers)
4. [Quick Start](#quick-start)
5. [Detailed Usage](#detailed-usage)
6. [Understanding Output](#understanding-output)
7. [Price Freshness System](#price-freshness-system)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Overview

Liquorfy uses automated scrapers to collect product and pricing data from 10 New Zealand liquor retailers. Each scraper:

- Fetches product catalog data (live HTTP, API calls, or browser automation)
- Parses product details (name, price, promotions, images, etc.)
- Upserts products and prices into the database
- Sweeps stale promotional pricing after each run
- Tracks changes and generates ingestion run reports

**Data Flow:**
```
Website/API → Scraper → Product Parser → Database Upsert
                             ↓
                    Promotion Detection        → Price freshness sweep
                    (via promo_utils)             (clear unseen promos)
```

---

## Prerequisites

### 1. Database Setup

Ensure PostgreSQL is running:

```bash
docker ps | grep postgres

# If not running:
docker-compose up -d postgres
```

### 2. Python Environment

```bash
cd /Users/axelmckenna/Liquorfy/api
poetry install

# Required for browser-based scrapers (Liquorland, Glengarry, Bottle O, Liquor Centre)
poetry run playwright install
```

### 3. Environment Variables

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/liquorfy
ENVIRONMENT=development
```

---

## Available Scrapers

| Chain | Key | Type | Pricing | Specials | Status |
|-------|-----|------|---------|---------|--------|
| Super Liquor | `super_liquor` | HTTP (selectolax) | Chain-wide | `/super-specials` + categories | ✅ Active |
| Liquorland | `liquorland` | Browser (Playwright) | Chain-wide (default prices only) | Digital mailer only — not scrapable | ✅ Active |
| Liquor Centre | `liquor_centre` | Browser + HTTP (CityHive) | Per-store (~90 stores) | `/category/specials` | ✅ Active |
| The Bottle O | `bottle_o` | HTTP (CityHive) + GTM fallback | Per-store | `/category/specials` | ✅ Active |
| New World | `new_world` | API (Foodstuffs/Algolia) | Per-store (all NZ stores) | `onPromotion` inline per product | ✅ Active |
| PakNSave | `paknsave` | API (Foodstuffs/Algolia) | Per-store (all NZ stores) | `onPromotion` inline per product | ✅ Active |
| Glengarry | `glengarry` | Browser (Playwright) | Chain-wide | Inline from product listings | ✅ Active |
| Thirsty Liquor | `thirsty_liquor` | Shopify JSON API | Chain-wide | `/collections/specials` | ✅ Active |
| Black Bull | `black_bull` | Shopify JSON API | Per-store (DB-backed list) | `/collections/specials` | ✅ Active |
| Countdown | `countdown` | API (Woolworths NZ) | Chain-wide | `isSpecial` inline per product | ✅ Active |

### Notes

**Liquorland:** 166 stores with per-store pricing, but per-store scraping requires complex browser UI automation (store selector modal). Currently captures only products with default/chain pricing. Products marked `no-cta` (requiring store selection) are skipped.

**Countdown:** Rebranded to Woolworths NZ (October 2023). `countdown.co.nz` still redirects; the live site and API are at `woolworths.co.nz`. Auth is cookieless — the scraper probes the API without cookies first. If the probe returns no items it captures session cookies via a plain HTTP GET (no browser, no JS) and retries once.

**Black Bull:** Per-store Shopify stores (60+ franchise locations). Only stores with active e-commerce subdomains are scraped. Store list is loaded from the `stores` DB table; falls back to a 3-store bootstrap list if the DB is empty.

**Bottle O:** Stores with CityHive subdomains (`{slug}.shop.thebottleo.co.nz`) get per-store pricing via HTTP. Stores without online shops fall back to the franchise GTM catalog at `thebottleo.co.nz`.

---

## Quick Start

### Option A: Run Everything

```bash
cd /Users/axelmckenna/Liquorfy/api

# Test one scraper first
poetry run python scripts/run_single_scraper.py super_liquor

# If successful, run all active scrapers
poetry run python scripts/run_all_scrapers.py --confirm
```

### Option B: Run Individual Scraper

```bash
cd /Users/axelmckenna/Liquorfy/api

# HTTP / API scrapers (fast, no browser needed)
poetry run python scripts/run_single_scraper.py super_liquor
poetry run python scripts/run_single_scraper.py new_world
poetry run python scripts/run_single_scraper.py paknsave
poetry run python scripts/run_single_scraper.py thirsty_liquor
poetry run python scripts/run_single_scraper.py black_bull
poetry run python scripts/run_single_scraper.py countdown

# Browser-based scrapers (slower, require Playwright)
poetry run python scripts/run_single_scraper.py liquorland
poetry run python scripts/run_single_scraper.py liquor_centre
poetry run python scripts/run_single_scraper.py bottle_o
poetry run python scripts/run_single_scraper.py glengarry
```

---

## Detailed Usage

### 1. Clear Old Price Data

**Purpose:** Remove stale price records before a fresh scrape.

**What it keeps:** Products, Stores, Ingestion Runs
**What it deletes:** All Price records

```bash
# Dry run (preview only)
poetry run python scripts/clear_price_data.py

# Actually delete
poetry run python scripts/clear_price_data.py --confirm
```

> **Note:** Under normal operation, clearing prices is rarely needed. The scraper upsert is idempotent and the freshness system handles stale promos automatically.

### 2. Run Single Scraper

```bash
poetry run python scripts/run_single_scraper.py <chain>
```

**Example Output:**
```
🚀 Running super_liquor scraper...

============================================================
✅ SCRAPER COMPLETED SUCCESSFULLY
============================================================
Status:        completed
Total items:   523
Changed items: 41
Failed items:  0
Duration:      0:01:46
============================================================
```

### 3. Run All Scrapers

```bash
# Dry run (preview plan)
poetry run python scripts/run_all_scrapers.py

# Execute
poetry run python scripts/run_all_scrapers.py --confirm
```

Scrapers run sequentially. If one fails, you are prompted to continue or abort. The final summary shows per-chain item counts and total duration.

---

## Understanding Output

### Scraper Metrics

| Metric | Description |
|--------|-------------|
| **Total items** | Products processed |
| **Changed items** | Products with price/data changes |
| **Failed items** | Products that errored |
| **Duration** | Wall-clock time for the run |

### Database Records

**Products table** — one row per unique product, identified by `(chain, source_product_id)`. Contains name, brand, category, ABV, volume, image URL.

**Prices table** — one row per `(product, store)`. Contains current price, promo price, promo text, member-only flag, `last_seen_at`, `promo_ends_at`.

**Stores table** — pre-populated store locations. Each store belongs to a chain.

**Ingestion Runs table** — historical log of all scraper runs (status, item counts, timestamps).

### Promotion Detection

Promotion data is extracted from:
- **HTML badge text** (Super Liquor, Glengarry, Liquorland) — parsed via `promo_utils.py`
- **API promotion objects** (New World, PakNSave) — `promotions[].rewardValue`, `decal`, `cardDependencyFlag`
- **Shopify `compare_at_price`** (Thirsty Liquor, Black Bull) — sale = `price < compare_at_price`
- **Shopify product tags** (`sale`, `special`, `clearance`, etc.)
- **Woolworths `isSpecial`** + `salePrice` (Countdown)
- **CityHive badge nodes** (Liquor Centre, Bottle O)

**Detected patterns:**
- `2 for $X` / `3 for $X` → calculated unit `promo_price_nzd`
- `Save $X` → `promo_price_nzd = price - save`
- `Members only` / `Clubcard` → `is_member_only = true`
- Date ranges (`Ends 31 Jan`) → `promo_ends_at`

---

## Price Freshness System

Three layers prevent stale or expired promo prices from being served:

### Layer 1: Scraper Mark-and-Sweep
After each successful scrape, promo fields (`promo_price_nzd`, `promo_text`, `promo_ends_at`) are cleared on any Price row for that chain/store that was **not seen** in the current run. This handles products whose promotions ended between scrapes.

- Chain-wide scrapers (Super Liquor, New World, PakNSave, Countdown, Glengarry, Thirsty Liquor) sweep the whole chain.
- Per-store scrapers (Liquor Centre, Bottle O, Black Bull) sweep each individual store after its batch completes.

### Layer 2: Periodic Expiry Cleanup
The worker loop (`api/app/workers/runner.py`) runs `run_promo_expiry_cleanup()` hourly. This NULLs promo fields on any Price row where `promo_ends_at < NOW()`, regardless of when the next scrape runs.

### Layer 3: Query-Time Guard
The search API (`api/app/services/search.py`) applies a SQL `CASE` expression so that `promo_price_nzd` is only used when `promo_ends_at IS NULL OR promo_ends_at > NOW()`. Expired promos are **never returned** to the frontend even if the DB hasn't been cleaned yet.

Prices older than 7 days are flagged with `is_stale: true` in the API response so the frontend can show a "price may be outdated" indicator.

---

## Troubleshooting

### Database Connection Error
```
sqlalchemy.exc.OperationalError: could not connect to server
```
```bash
docker-compose up -d postgres
```

### Playwright Not Installed
```
playwright._impl._api_types.Error: Executable doesn't exist
```
```bash
poetry run playwright install chromium
```

### High Failed Items Count

Check for site structure changes or rate limiting:
```bash
poetry run python scripts/run_single_scraper.py <chain> 2>&1 | tee scraper.log
grep "ERROR" scraper.log | head -20
```

### Countdown Returns No Items

The scraper probes cookieless first. If Woolworths starts requiring auth:
1. Check that `woolworths.co.nz` is reachable (not geo-blocked in CI)
2. The HTTP cookie grab (`_get_cookies_direct`) should handle session tokens automatically
3. If the API contract changes, inspect the response structure vs the `products.items` path

### New World / PakNSave Auth Failure

These scrapers obtain a guest JWT via `POST /api/user/get-current-user`. If this fails:
- The scraper falls back to browser-based token capture (slower, requires Playwright)
- If both fail, the run is aborted with `status=failed`

---

## Best Practices

### Scraping Schedule

| Frequency | Action |
|-----------|--------|
| Hourly | Promo expiry cleanup (automatic via worker) |
| Daily | Full scrape of all active chains |
| On-demand | Single-chain scrape when specific data is needed |

```bash
# Daily scrape at 2 AM
0 2 * * * cd /path/to/Liquorfy/api && poetry run python scripts/run_all_scrapers.py --confirm
```

### Run Order

Faster scrapers first:
1. `thirsty_liquor`, `black_bull` (Shopify API — very fast)
2. `new_world`, `paknsave` (Foodstuffs API — fast)
3. `super_liquor` (HTTP — fast)
4. `liquorland`, `glengarry` (Browser — moderate)
5. `liquor_centre`, `bottle_o` (Browser + HTTP — slow, many stores)

### Monitoring

```bash
# Latest ingestion runs
psql $DATABASE_URL -c "
SELECT chain, status, items_total, items_changed, items_failed, started_at
FROM ingestion_runs
ORDER BY started_at DESC
LIMIT 15;
"

# Price freshness by chain
psql $DATABASE_URL -c "
SELECT
    chain,
    COUNT(*) as price_rows,
    COUNT(promo_price_nzd) as with_promo,
    MAX(last_seen_at) as last_scraped
FROM prices p
JOIN stores s ON p.store_id = s.id
GROUP BY chain
ORDER BY last_scraped DESC;
"
```

### Database Backups

```bash
docker exec infra-db-1 pg_dump -U postgres liquorfy > backup_$(date +%Y%m%d).sql
```

---

## Adding a New Scraper

1. Create `api/app/scrapers/<chain>.py` extending `Scraper` (HTTP/API) or `BrowserScraper` (Playwright)
2. Implement `fetch_catalog_pages()` and `parse_products()` (or override `run()` for API-based scrapers)
3. Set `chain = "<chain_name>"` and `_sweep_per_store = True` if pricing is per-store
4. Register in `api/app/scrapers/registry.py`

**Reference implementations:**
- Simple HTTP: `super_liquor.py`
- Shopify JSON API: `thirsty_liquor.py`
- Shopify per-store: `black_bull.py`
- Algolia/API per-store: `foodstuffs_base.py` + `new_world_api.py`
- CityHive per-store: `liquor_centre.py`
- Browser (Playwright): `glengarry.py`
