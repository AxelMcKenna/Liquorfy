# Store Locations Coverage Documentation

**Last Updated:** 2026-01-01

## Overall Coverage Summary

**Last Database Audit:** 2026-01-01 11:21

| Store Chain      | We Have | Expected | Coverage | Gap to 90% | Status |
|------------------|---------|----------|----------|------------|--------|
| Super Liquor     | 131     | 140      | 93.6%    | -5 stores  | ✅     |
| Liquor Centre    | 0       | 240      | 0.0%     | +216       | ❌     |
| Liquorland       | 0       | 170      | 0.0%     | +153       | ❌     |
| New World        | 0       | 150      | 0.0%     | +135       | ❌     |
| Bottle O         | 0       | 114      | 0.0%     | +102       | ❌     |
| Thirsty Liquor   | 0       | 106      | 0.0%     | +95        | ❌     |
| PAK'nSAVE        | 0       | 61       | 0.0%     | +54        | ❌     |
| Black Bull       | 0       | 59       | 0.0%     | +53        | ❌     |
| Big Barrel       | 0       | 51       | 0.0%     | +45        | ❌     |
| Glengarry        | 0       | 18       | 0.0%     | +16        | ❌     |
| **TOTAL**        | **131** | **1109** | **11.8%** | **+867**   |        |

### Summary Statistics
- ✅ **Chains completed (≥90%):** 1/10 (10%)
- 🟡 **Chains partial (50-89%):** 0/10 (0%)
- 🟠 **Chains started (1-49%):** 0/10 (0%)
- ❌ **Chains missing (0%):** 9/10 (90%)

### To Reach 90% Overall Coverage
Need **867 additional stores** across 9 chains

---

## Super Liquor (94% Coverage)

### Summary
- **Total Expected:** 140 stores
- **Currently Loaded:** 131 stores
- **Missing:** 9 stores (6% gap)
- **Target:** 90%+ ✅ **Achieved**

### Data Collection Methods

#### 1. API Scraping
- **Endpoint:** `https://www.superliquor.co.nz/getstorelocatordetails`
- **Results:** Only 40 stores returned (regardless of region filter)
- **Quality:** Complete data (coordinates, addresses, phone numbers)
- **Coverage:** 16 stores unique to API (not in website dropdown)

#### 2. Website Dropdown Scraping
- **Source:** Store selector dropdown on website
- **Results:** 118 stores found
- **Method:** Scraped dropdown options with Playwright
- **File:** `/Users/axelmckenna/Liquorfy/api/data/all_super_liquor_stores_scraped.json`

#### 3. City-Name Geocoding
- **Method:** Extract city/suburb from store name, geocode via Nominatim
- **Success Rate:** 113/118 (95.8%)
- **Failed:** 5 stores (shopping centers/subdivisions not in OpenStreetMap)
- **File:** `/Users/axelmckenna/Liquorfy/api/data/super_liquor_geocoded.json`

### Known Missing Stores (3)

These stores exist on the Super Liquor website but are **NOT in database**:

#### 1. Super Liquor Pacific Square, Manukau
- **URL:** https://pacificsquare.superliquor.co.nz
- **Status:** Failed geocoding - shopping center name
- **Likely Location:** Manukau, Auckland
- **Recommended Fix:**
  - Google Places API search for "Pacific Square Manukau"
  - Manual geocoding using Google Maps
  - Approximate coordinates: Manukau city center

#### 2. Super Liquor Raumati Village
- **URL:** https://raumativillage.superliquor.co.nz
- **Status:** Failed geocoding - "Raumati Village" not in OSM
- **Likely Location:** Raumati Beach or Raumati South, Kapiti Coast
- **Recommended Fix:**
  - Try geocoding "Raumati Beach, New Zealand"
  - Or use coordinates for Raumati South
  - Shopping center likely near beach area

#### 3. Super Liquor Tahunanui South
- **URL:** https://tahunanui.superliquor.co.nz
- **Status:** Failed geocoding - "Tahunanui South" not in OSM
- **Likely Location:** Nelson area (southern part of Tahunanui suburb)
- **Note:** "Super Liquor Tahunanui" (without "South") IS in database
- **Recommended Fix:**
  - May be duplicate of existing Tahunanui store
  - Check if there are actually two stores in Tahunanui
  - Use Tahunanui coordinates if only one store exists

### Stores in Database NOT in Website Scrape (16)

These stores came from the API but weren't in the website dropdown:

1. Super Liquor Avondale
2. Super Liquor Balmoral
3. Super Liquor Botany
4. Super Liquor Bryant Park
5. Super Liquor Bulls
6. Super Liquor Burswood
7. Super Liquor Carterton
8. Super Liquor Coromandel
9. Super Liquor Dairy Flat
10. Super Liquor Dannevirke
11. Super Liquor Dargaville
12. Super Liquor Devon Street
13. Super Liquor Dinsdale
14. Super Liquor Flagstaff
15. Super Liquor Forrest Hill
16. Super Liquor Geraldine

**Status:** ✅ All 16 have complete coordinates and are fully loaded

### Unknown Missing Stores (6)

**Calculation:** 140 expected - 131 in DB - 3 known missing = **6 unaccounted**

These stores are completely unaccounted for in any data source:
- Not in website dropdown (118 stores)
- Not in API results (40 stores, 16 unique)
- Not in database

**Possible Explanations:**
- Recently opened stores not yet on website
- Franchise/partner stores with different URLs or branding
- Stores that closed but still counted in "140 expected" total
- Duplicate entries (e.g., relocated stores counted twice)
- Stores trading under different names
- Seasonal/temporary locations

**Recommended Actions:**
1. Contact Super Liquor directly for official store list
2. Check business directories (Google Maps, Yellow Pages)
3. Review Super Liquor's official "Find a Store" page for any missed entries
4. Verify if 140 is the current accurate count

### Data Reconciliation

**How we got 131 stores:**
- 113 stores from successful city-name geocoding
- 16 stores from API (not in website scrape)
- 2 stores that "failed" geocoding but ended up in DB (Alice Town, Central Park Village)
- **Total:** 113 + 16 + 2 = **131** ✓

**The Missing 9:**
- 3 known (failed geocoding, can be manually added)
- 6 unknown (need investigation)

### Next Steps for Super Liquor

**To reach 95%+ (add 3 stores):**
1. ✅ **Achieved 94%** - Already at target!
2. Manually geocode Pacific Square, Manukau
3. Manually geocode Raumati Village
4. Investigate Tahunanui South (possible duplicate)

**To reach 100% (add 9 stores):**
1. Complete the 3 known stores above
2. Investigate and identify the 6 unknown stores
3. Verify total expected count is accurate (140)

---

## Big Barrel (0% Coverage)

### Summary
- **Total Expected:** 51 stores
- **Currently Loaded:** 0 stores
- **Target:** 90%+ (46 stores needed)

### Status
🔴 **Not Started**

### Recommended Approach
1. Check for API endpoint (similar to Super Liquor)
2. Scrape website store locator
3. Apply city-name geocoding method (proven successful for Super Liquor)

---

## Glengarry (0% Coverage)

### Summary
- **Total Expected:** 18 stores
- **Currently Loaded:** 0 stores
- **Target:** 90%+ (17 stores needed)

### Status
🔴 **Not Started**

### Recommended Approach
1. Check for API endpoint
2. Scrape website store locator
3. Apply city-name geocoding method
4. Small store count makes manual geocoding feasible as backup

---

## Liquor Centre (0% Coverage)

### Summary
- **Total Expected:** 240 stores
- **Currently Loaded:** 0 stores
- **Target:** 90%+ (216 stores needed)

### Status
🔴 **Not Started**

### Notes
- Largest chain by count
- May require multiple data sources
- High-priority for overall coverage improvement

---

## Liquorland (0% Coverage)

### Summary
- **Total Expected:** 170 stores
- **Currently Loaded:** 0 stores
- **Target:** 90%+ (153 stores needed)

### Status
🔴 **Not Started**

---

## New World (0% Coverage)

### Summary
- **Total Expected:** 150 stores
- **Currently Loaded:** 0 stores
- **Target:** 90%+ (135 stores needed)

### Status
🔴 **Not Started**

### Notes
- Part of Foodstuffs network
- May have API access similar to PAK'nSAVE

---

## Bottle O (0% Coverage)

### Summary
- **Total Expected:** 114 stores
- **Currently Loaded:** 0 stores
- **Target:** 90%+ (103 stores needed)

### Status
🔴 **Not Started**

---

## Thirsty Liquor (0% Coverage)

### Summary
- **Total Expected:** 106 stores
- **Currently Loaded:** 0 stores
- **Target:** 90%+ (96 stores needed)

### Status
🔴 **Not Started**

---

## PAK'nSAVE (0% Coverage)

### Summary
- **Total Expected:** 61 stores
- **Currently Loaded:** 0 stores
- **Target:** 90%+ (55 stores needed)

### Status
🔴 **Not Started**

### Notes
- Part of Foodstuffs network
- Likely has API similar to New World

---

## Black Bull (0% Coverage)

### Summary
- **Total Expected:** 59 stores
- **Currently Loaded:** 0 stores
- **Target:** 90%+ (54 stores needed)

### Status
🔴 **Not Started**

---

## General Methods & Lessons Learned

### Successful Approaches (from Super Liquor)

#### 1. City-Name Geocoding
**Success Rate:** 95.8%

**Method:**
```python
# Extract city name from store name
store_name = "Super Liquor Alexandra"
city = store_name.replace("Super Liquor ", "").strip()  # "Alexandra"

# Geocode with just city + country
query = f"{city}, New Zealand"
coords = geocode_nominatim(query)
```

**Pros:**
- Works for most NZ cities/suburbs in OpenStreetMap
- Free (Nominatim/OSM)
- Fast processing
- No API keys needed

**Cons:**
- Fails for shopping centers (e.g., "Pacific Square")
- Fails for subdivisions not in OSM
- Gives city center, not exact store location
- Requires 1-2 second rate limiting

**Best For:** Stores named after suburbs/towns

#### 2. API Scraping
**Coverage:** Variable by chain

**Pros:**
- Complete, accurate data
- Includes addresses, phones, coordinates
- Fast bulk retrieval

**Cons:**
- Not all chains have public APIs
- May have incomplete data (Super Liquor API only had 40/140 stores)
- May require authentication
- Rate limiting

**Best For:** Chains with documented APIs

#### 3. Website Dropdown Scraping
**Coverage:** Good for store lists

**Pros:**
- Comprehensive store names
- Often has all locations
- Relatively stable HTML structure

**Cons:**
- Doesn't always include coordinates
- May require JavaScript rendering (Playwright)
- Need to handle pagination/regions
- May miss newly added stores

**Best For:** Getting complete store name lists

### Tools & Technologies

- **Geocoding:** Nominatim (OpenStreetMap) - Free, 1 req/sec limit
- **Web Scraping:** Playwright (headless browser)
- **Alternative Geocoding:** Google Places API (paid, more accurate for businesses)
- **Database:** PostgreSQL with PostGIS
- **Language:** Python with asyncio for concurrent requests

### Rate Limiting Guidelines

- **Nominatim:** 1 request per second (strict)
- **Website Scraping:** 1-2 seconds between requests (be respectful)
- **APIs:** Check documentation, typically more lenient

---

## Scripts Reference

### Super Liquor Scripts

| Script | Purpose | Location |
|--------|---------|----------|
| Store dropdown scraper | Get all store names | `scripts/scrape_super_liquor_dropdown.py` |
| City-name geocoder | Geocode by city | `scripts/geocode_by_city_name.py` |
| Dataset merger | Combine sources | `scripts/merge_super_liquor_datasets.py` |
| Database loader | Load to DB | `scripts/load_merged_super_liquor.py` |
| Coverage summary | Generate report | `scripts/final_store_summary.py` |

### Data Files

| File | Contents | Records |
|------|----------|---------|
| `data/all_super_liquor_stores_scraped.json` | Website dropdown scrape | 118 stores |
| `data/super_liquor_geocoded.json` | Geocoded stores | 113 with coords |
| `data/super_liquor_merged.json` | Final merged dataset | 113 stores |

---

## Database Schema

```sql
CREATE TABLE stores (
    id SERIAL PRIMARY KEY,
    api_id VARCHAR,
    name VARCHAR NOT NULL,
    chain VARCHAR NOT NULL,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    address VARCHAR,
    region VARCHAR,
    url VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_stores_chain ON stores(chain);
CREATE INDEX idx_stores_location ON stores(lat, lon);
```

---

## Progress Tracking

### Completed
- ✅ Super Liquor: 94% coverage (131/140 stores)

### In Progress
- None

### To Do (Priority Order)
1. 🔴 Liquor Centre (240 stores) - Largest impact
2. 🔴 Liquorland (170 stores)
3. 🔴 New World (150 stores)
4. 🔴 Bottle O (114 stores)
5. 🔴 Thirsty Liquor (106 stores)
6. 🔴 PAK'nSAVE (61 stores)
7. 🔴 Black Bull (59 stores)
8. 🔴 Big Barrel (51 stores)
9. 🔴 Glengarry (18 stores)

### Milestone Goals

**Phase 1: Quick Wins (Target: 25% overall)**
- Complete smaller chains: Glengarry, Big Barrel
- Total: 131 + 18 + 51 = 200 stores (18% coverage)

**Phase 2: Major Chains (Target: 50% overall)**
- Add: New World, PAK'nSAVE (both Foodstuffs)
- Total: ~350 stores (31% coverage)

**Phase 3: Full Coverage (Target: 90% overall)**
- Complete all chains to 90%+ each
- Total: ~1000 stores (90%+ coverage)
