# Store Collection Status

**Last Updated:** 2026-01-01
**Total Stores in Database:** 1,051

## Summary

We have successfully collected store data for **all 11 supported chains**. All chains now have sufficient store data for product scraping.

### Stores in Database

| Chain | Count | Status | Coordinates | Notes |
|-------|-------|--------|-------------|-------|
| **Countdown** | 186 | ✅ Complete | Placeholder (0,0) | Scraped from Woolworths API - has names, suburbs, postcodes |
| **Liquorland** | 167 | ✅ Complete | Full geocoded | Full addresses with real lat/lon coordinates |
| **Bottle-O** | 152 | ✅ Complete | Placeholder (0,0) | Scraped from shop.thebottleo.co.nz - has addresses from Google Maps links |
| **New World** | 144 | ✅ Complete | Placeholder (0,0) | API-based chain - has store IDs |
| **Super Liquor** | 131 | ✅ Complete | Full geocoded | Full addresses with real lat/lon coordinates |
| **Liquor Centre** | 90 | ✅ Complete | Placeholder (0,0) | API-based chain - has store slugs |
| **Pak'nSave** | 57 | ✅ Complete | Placeholder (0,0) | API-based chain - has store IDs |
| **Black Bull** | 56 | ✅ Complete | Full geocoded | Full addresses with real lat/lon coordinates |
| **Big Barrel** | 46 | ✅ Complete | Full geocoded | Full addresses with real lat/lon coordinates |
| **Thirsty Liquor** | 11 | ✅ Complete | Placeholder (0,0) | Delivery zones/hubs - limited coverage |
| **Glengarry** | 9 | ✅ Complete | Full geocoded | Full addresses with real lat/lon coordinates |

**TOTAL:** 1,051 stores

## API-Based vs Location-Based Chains

### API-Based Chains (Don't Need Exact Coordinates)

These chains use API-based product scrapers that work with **store IDs**, not geographic coordinates:

- **New World** - Uses store ID from database `api_id` field
- **Pak'nSave** - Uses store ID from database `api_id` field
- **Liquor Centre** - Uses store slugs from database `api_id` field
- **Countdown** - Associates products with all Countdown stores (no store-specific scraping)

**Why placeholder coordinates are acceptable:**
When scraping products, we pass the store ID to the API (e.g., `storeId: "60928d93-06fa-4d8f-92a6-8c359e7e846d"`), not latitude/longitude. The coordinates are only used for:
1. Store locator features (future feature)
2. Geographic analysis (not critical for MVP)

**Current Implementation:**
- Stores loaded with `lat: 0.0, lon: 0.0` as placeholder
- `api_id` field contains the actual store identifier used for product scraping
- `address` field contains city name or general location

### Location-Based Chains (Have Full Geocoded Coordinates)

These chains use browser-based scrapers that navigate to physical store pages:

- **Liquorland** ✅ (167 stores)
- **Super Liquor** ✅ (131 stores)
- **Black Bull** ✅ (56 stores)
- **Big Barrel** ✅ (46 stores)
- **Glengarry** ✅ (9 stores)

## Known Limitations & Data Quality Issues

### 1. Placeholder Coordinates for Most Chains

**Chains Affected:** Countdown, Bottle-O, New World, Pak'nSave, Liquor Centre, Thirsty Liquor (886 stores / 84% of total)

**Impact:**
- ✅ **Low impact for product scraping** - These chains use API-based or chain-wide scraping
- ⚠️ **High impact for store locator features** - Cannot show accurate store locations on map
- ⚠️ **High impact for distance calculations** - Cannot find nearest store to user

**Why we have placeholders:**
- API-based chains only provide store IDs, not full addresses
- Countdown API only returns suburb/postcode, not street addresses
- Geocoding 886 stores would require significant effort and may hit rate limits

**Future Fix:**
- Manually geocode using Google Maps Geocoding API (costs ~$5 per 1000 requests)
- Or scrape individual store detail pages for full addresses
- Or accept limitation and only show stores by region/suburb

### 2. Thirsty Liquor Limited Coverage

**Issue:** Only 11 stores vs ~130+ physical Thirsty Liquor locations nationwide

**Root Cause:** The scraper found "delivery zones" from their website (`window.storeData`), not physical store locations. Each delivery zone represents a hub covering multiple regions.

**Impact:**
- ⚠️ **Medium impact** - Missing ~90% of Thirsty Liquor stores
- Some regions may have no nearby Thirsty Liquor in store locator
- Product prices may not reflect local store availability

**Workaround:** Current 11 delivery hubs cover main regions (Auckland, Wellington, Christchurch, etc.)

**Future Fix:**
- Find alternative data source (store locator page, sitemap, business directories)
- Or scrape from their parent company websites
- Or manually compile from public business listings

### 3. Missing Store Metadata

**What's Missing:**
- ❌ Store hours/opening times
- ❌ Phone numbers
- ❌ Store amenities (parking, wheelchair access, etc.)
- ❌ Store photos
- ❌ Department info (has pharmacy, bakery, etc.)

**Impact:**
- ⚠️ **Medium impact** - Reduces usefulness of store locator feature
- Users cannot see if store is currently open
- Cannot call store to check stock

**Future Enhancement:**
- Scrape store detail pages for this metadata
- Or use Google Places API to enrich store data
- Or crowdsource from users

### 4. No Address Standardization

**Issue:** Store addresses are inconsistent formats from different sources

Examples:
- "Albany, AUK 0632" (Countdown - suburb only)
- "225 Dairy Flat Highway, Albany Village, Albany Auckland 0632" (Bottle-O - full address)
- "Albany" (New World - name only)

**Impact:**
- ⚠️ **Low impact for MVP** - Stores still identifiable
- ⚠️ **Medium impact for geocoding** - Hard to standardize coordinates later

**Future Fix:**
- Parse and normalize all addresses to NZ Post standard format
- Use address validation API (NZ Post, HERE, Google)

### 5. Bottle-O vs Big Barrel Overlap

**Clarification:** These are **separate chains** despite both being Lion NZ owned:
- **Big Barrel** - 46 stores (in database as "big_barrel")
- **Bottle-O** - 152 stores (in database as "bottle_o")

Both have independent product scrapers and store networks. No action needed.

### 6. Product Scraper Coverage

**Chains WITH product scrapers:**
- ✅ Countdown (countdown_api.py)
- ✅ Super Liquor (super_liquor.py)
- ✅ New World (new_world_api.py)
- ✅ Pak'nSave (paknsave_api.py)
- ✅ Glengarry (glengarry.py)
- ✅ Liquor Centre (liquor_centre.py)
- ✅ Black Bull (black_bull.py)
- ✅ Thirsty Liquor (thirsty_liquor.py)

**Chains MISSING product scrapers:**
- ❌ **Bottle-O** - Has store scraper (bottle_o.py) but no product scraper yet
- ❌ **Liquorland** - Has stores but no product scraper yet
- ❌ **Big Barrel** - Has stores but no product scraper yet

**Impact:**
- ⚠️ **High impact** - Cannot compare prices for 365 stores (35% of database)
- Missing major chains reduces value proposition

**Next Steps:**
- Implement product scrapers for missing chains
- Bottle-O likely uses same API as their online shop
- Liquorland and Big Barrel may need browser-based scraping

## Database Schema

```sql
Table "public.stores"
   Column   |           Type           | Notes
------------+--------------------------+-------
 id         | uuid                     | Primary key
 name       | character varying(255)   | Store display name
 chain      | character varying(64)    | Chain identifier
 lat        | double precision         | Latitude (0.0 for API-based stores)
 lon        | double precision         | Longitude (0.0 for API-based stores)
 address    | character varying(255)   | Full address or city name
 region     | character varying(64)    | Region/area code
 url        | character varying(255)   | Store-specific URL
 api_id     | character varying(255)   | API identifier for API-based chains
 created_at | timestamp with time zone |
 updated_at | timestamp with time zone |

Indexes:
 - stores_pkey PRIMARY KEY (id)
 - uq_store_chain_api_id UNIQUE (chain, api_id)
 - uq_store_chain_name UNIQUE (chain, name)
```

## Recent Changes (2026-01-01)

### ✅ Countdown Stores Added (186 stores)

**Method:** Scraped from Woolworths NZ API (api.cdx.nz/site-location)
- Found store data by searching with empty query
- Extracted store ID, name, suburb, state, postcode
- No full addresses or coordinates available from API
- Imported with placeholder coordinates (0,0)

**Files:**
- Scraper: `app/store_scrapers/countdown_stores_final.py`
- Import script: `scripts/import_countdown_stores.py`
- Data: `app/data/countdown_stores.json`

### ✅ Thirsty Liquor Stores Added (11 stores)

**Method:** Extracted from `window.storeData` on thirstyliquor.co.nz
- Found delivery zones/hubs, not individual stores
- Each hub serves multiple regions
- Limited to 11 locations vs ~130+ actual stores

**Files:**
- Scraper: `app/store_scrapers/thirsty_liquor.py`
- Runner: `run_missing_store_scrapers.py`

### ✅ Bottle-O Stores Added (152 stores)

**Method:** Scraped from shop.thebottleo.co.nz/change store selector
- Extracted from `[class*="StoreCard"]` HTML elements
- Got addresses from Google Maps direction links
- Deduplicated by URL (314 raw → 157 unique → 152 saved after name dedup)
- Placeholder coordinates (0,0) - addresses available but not geocoded

**Files:**
- Scraper: `app/store_scrapers/bottle_o.py` (updated to parse HTML)
- Runner: `run_bottle_o_only.py`

## Recommendations

### ✅ Completed

1. ✅ **All store scrapers run** - 11/11 chains have stores
2. ✅ **Countdown stores loaded** - Used Woolworths API successfully
3. ✅ **Bottle-O scraper fixed** - HTML parsing with deduplication
4. ✅ **Thirsty Liquor loaded** - Limited to delivery zones

### High Priority (Blocks MVP)

1. **⚠️ Implement missing product scrapers**
   - Bottle-O (152 stores)
   - Liquorland (167 stores)
   - Big Barrel (46 stores)
   - **Total: 365 stores (35%) cannot provide prices**

2. **Geocode Countdown stores** (186 stores)
   - Have suburb + postcode, need full addresses
   - Could use NZ business directories or manual lookup
   - Required for store locator feature

3. **Complete Thirsty Liquor coverage** (missing ~120 stores)
   - Find alternative data source
   - Or accept current coverage of main hubs

### Medium Priority (Improves UX)

4. **Geocode Bottle-O stores** (152 stores)
   - Have full addresses from Google Maps links
   - Just need to run geocoding API
   - Moderate effort, high value for store locator

5. **Add store metadata** (hours, phones, amenities)
   - Scrape from store detail pages
   - Or use Google Places API
   - Nice-to-have for v1.1

6. **Standardize addresses**
   - Parse to consistent format
   - Validate with NZ Post
   - Helps with geocoding accuracy

### Low Priority (Future Enhancement)

7. **Automated store updates**
   - Schedule scrapers weekly/monthly
   - Detect new stores and closures
   - Keep data fresh

8. **Store photos**
   - Scrape from websites or Google
   - Improves store locator appeal

9. **Store reviews/ratings**
   - Aggregate from Google, Facebook
   - Or allow user submissions

## Running Scrapers

### Run All Missing Store Scrapers

```bash
cd /Users/axelmckenna/Liquorfy/api
PYTHONPATH=/Users/axelmckenna/Liquorfy/api \
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/liquorfy \
poetry run python run_missing_store_scrapers.py
```

### Import Countdown Stores

```bash
cd /Users/axelmckenna/Liquorfy/api
PYTHONPATH=/Users/axelmckenna/Liquorfy/api \
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/liquorfy \
poetry run python scripts/import_countdown_stores.py
```

### Run Individual Store Scraper

```bash
cd /Users/axelmckenna/Liquorfy/api
PYTHONPATH=/Users/axelmckenna/Liquorfy/api \
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/liquorfy \
poetry run python scripts/scrape_single_chain.py <chain_name>

# Available chains: liquorland, super_liquor, glengarry, bottle_o, black_bull, thirsty_liquor
```

## Files Reference

### Scrapers
- `app/store_scrapers/base.py` - Base scraper class
- `app/store_scrapers/countdown_stores_final.py` - Countdown via CDX API
- `app/store_scrapers/bottle_o.py` - Bottle-O HTML parser
- `app/store_scrapers/thirsty_liquor.py` - Thirsty Liquor window.storeData
- `app/store_scrapers/*.py` - Other chain scrapers

### Scripts
- `scripts/import_countdown_stores.py` - Import Countdown from JSON
- `run_missing_store_scrapers.py` - Run Bottle-O and Thirsty Liquor
- `run_bottle_o_only.py` - Test Bottle-O scraper in isolation

### Data Files
- `app/data/countdown_stores.json` - Countdown stores from CDX API
- `app/data/newworld_stores.json` - New World store IDs
- `app/data/paknsave_stores.json` - Pak'nSave store IDs
- `app/data/liquor_centre_stores.json` - Liquor Centre store slugs

## Questions?

If you need to modify store collection strategy, consider:
1. What is the store data needed for? (Product scraping vs store locator)
2. Does the chain use API-based or location-based product scraping?
3. Are exact coordinates required for the use case?
4. Is the data quality worth the engineering effort?
5. What's the MVP scope vs nice-to-have features?
