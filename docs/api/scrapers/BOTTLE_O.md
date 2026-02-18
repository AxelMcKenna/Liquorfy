# The Bottle O Scraper

## Overview

Scraper for The Bottle O NZ using a dual-strategy approach:
- **Primary:** Per-store CityHive HTTP scraping (`{slug}.shop.thebottleo.co.nz`)
- **Fallback:** Franchise GTM catalog extraction (`thebottleo.co.nz` via Playwright)

## Implementation

- **File:** `api/app/scrapers/bottle_o.py`
- **Chain:** `bottle_o`
- **Platform:** CityHive (same as Liquor Centre)

## Strategy

Individual Bottle O stores run on the CityHive platform at `{slug}.shop.thebottleo.co.nz` with per-store pricing. The scraper:

1. Loads all Bottle O store URLs from the `stores` DB table
2. For each store URL matching `*.shop.thebottleo.co.nz`:
   - Scrapes each category via HTTP (`/category/{name}`)
   - Parses product cards using selectolax (no browser needed)
   - Upserts prices to that specific store
   - Sweeps stale promos after each store's batch
3. For stores **without** a CityHive subdomain, falls back to the franchise catalog at `thebottleo.co.nz` via Playwright + GTM dataLayer extraction

## Categories Scraped

`beer`, `wine`, `spirits`, `cider`, `rtds`, `specials`

The `specials` category is scraped first so subsequent category pages can overwrite with correct was/now pricing where applicable.

## Features

- ✅ Per-store pricing via CityHive HTTP API
- ✅ Promotions extracted (badge text, was-price, multi-buy deals)
- ✅ `specials` category endpoint
- ✅ Promo mark-and-sweep after each store's scrape
- ✅ Playwright fallback for stores without CityHive subdomains
- ✅ Rate limiting (2.5s between categories, 1.5s between requests)

## Robots.txt Compliance

- **User Agent:** `Liquorfy/1.0 (Price Comparison Bot; +https://liquorfy.co.nz)`
- **Paths accessed:** `/category/{name}` only (not disallowed)
- **Rate limiting:** 2.5s between category requests

## Known Limitations

1. **Image URLs:** CityHive product images may not always be present
2. **GTM fallback coverage:** The franchise catalog has no per-store pricing — all stores get the same fallback price
3. **Store list dependency:** Requires stores to be populated in the `stores` DB table with valid CityHive subdomain URLs

## Usage

```python
from app.scrapers.bottle_o import BottleOScraper

scraper = BottleOScraper()
run = await scraper.run()
print(f"Scraped {run.items_total} products")
```

```bash
# Via CLI
poetry run python scripts/run_single_scraper.py bottle_o
```
