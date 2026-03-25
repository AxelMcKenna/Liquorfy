# Liquorfy Database Schema

## Current State Summary

### Products by Chain
| Chain | Products | Stores | Prices | Top Categories |
|-------|----------|--------|--------|----------------|
| **Liquor Centre** | 8,868 | 9 | 10,073 | beer (900), red_wine (704), white_wine (698) |
| **Super Liquor** | 1,329 | 4 | 8,671 | white_wine (174), red_wine (152), gin (127) |
| **Bottle-O** | 204 | 2 | 408 | Beer/Premium Craft (31), RTD/Vodka (30), Wine/Red (20) |
| **Liquorland** | 175 | 4 | 748 | vodka (21), gin (19), whisky (18) |
| **Countdown** | 2 | 4 | 2 | beer (1), gin (1) |
| **TOTAL** | **10,578** | **23** | **19,902** | - |

### Database Statistics
- **Total Unique Products:** 10,578
- **Total Stores:** 23
- **Total Price Records:** 19,902
- **Total Chains:** 5
- **Categories:** 28 distinct categories
- **Categorization Rate:** 87.6% (Liquor Centre), varies by chain

---

## Entity Relationship Diagram

```
┌─────────────────┐
│     STORES      │
├─────────────────┤
│ id (PK)         │ UUID
│ name            │ VARCHAR(255)
│ chain           │ VARCHAR(64)
│ lat             │ DOUBLE
│ lon             │ DOUBLE
│ address         │ VARCHAR(255)
│ region          │ VARCHAR(64)
│ url             │ VARCHAR(255)
│ created_at      │ TIMESTAMP
│ updated_at      │ TIMESTAMP
└─────────────────┘
         │
         │ 1
         │
         │ N
         ▼
┌─────────────────┐
│     PRICES      │
├─────────────────┤
│ id (PK)         │ UUID
│ product_id (FK) │ UUID ────┐
│ store_id (FK)   │ UUID     │
│ currency        │ VARCHAR(3)│
│ price_nzd       │ DOUBLE   │
│ promo_price_nzd │ DOUBLE   │
│ promo_text      │ VARCHAR  │
│ promo_ends_at   │ TIMESTAMP│
│ last_seen_at    │ TIMESTAMP│
│ price_last_chg  │ TIMESTAMP│
│ is_member_only  │ BOOLEAN  │
│ created_at      │ TIMESTAMP│
│ updated_at      │ TIMESTAMP│
└─────────────────┘          │
                              │
                              │ N
                              │
                              │ 1
                              ▼
                    ┌─────────────────┐
                    │    PRODUCTS     │
                    ├─────────────────┤
                    │ id (PK)         │ UUID
                    │ chain           │ VARCHAR(64)
                    │ source_prod_id  │ VARCHAR(128)
                    │ name            │ VARCHAR(255)
                    │ brand           │ VARCHAR(128)
                    │ category        │ VARCHAR(64)
                    │ abv_percent     │ DOUBLE
                    │ pack_count      │ INTEGER
                    │ unit_volume_ml  │ DOUBLE
                    │ total_volume_ml │ DOUBLE
                    │ image_url       │ VARCHAR(512)
                    │ product_url     │ VARCHAR(512)
                    │ created_at      │ TIMESTAMP
                    │ updated_at      │ TIMESTAMP
                    └─────────────────┘
                              │
                              │ 1
                              │
                              │ N
                              ▼
                    ┌─────────────────┐
                    │ INGESTION_RUNS  │
                    ├─────────────────┤
                    │ id (PK)         │ UUID
                    │ chain           │ VARCHAR(64)
                    │ status          │ VARCHAR(32)
                    │ started_at      │ TIMESTAMP
                    │ finished_at     │ TIMESTAMP
                    │ items_total     │ INTEGER
                    │ items_changed   │ INTEGER
                    │ items_failed    │ INTEGER
                    │ log_url         │ VARCHAR(255)
                    │ created_at      │ TIMESTAMP
                    │ updated_at      │ TIMESTAMP
                    └─────────────────┘
```

---

## Table Schemas

### 1. **products**
Master table for all products across all chains.

**Primary Key:** `id` (UUID)
**Unique Constraint:** `(chain, source_product_id)`

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | NOT NULL | Primary key |
| chain | VARCHAR(64) | NOT NULL | Chain identifier (liquor_centre, super_liquor, etc.) |
| source_product_id | VARCHAR(128) | NOT NULL | Product ID from source website |
| name | VARCHAR(255) | NOT NULL | Product name |
| brand | VARCHAR(128) | NULL | Inferred brand name |
| category | VARCHAR(64) | NULL | Inferred category (beer, wine, spirits, etc.) |
| abv_percent | DOUBLE | NULL | Alcohol by volume percentage |
| pack_count | INTEGER | NULL | Number of items in pack |
| unit_volume_ml | DOUBLE | NULL | Volume per unit in milliliters |
| total_volume_ml | DOUBLE | NULL | Total volume (pack_count × unit_volume) |
| image_url | VARCHAR(512) | NULL | Product image URL |
| product_url | VARCHAR(512) | NULL | Product page URL |
| created_at | TIMESTAMP | NOT NULL | Record creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `(chain, source_product_id)`
- BTREE on `chain` (`ix_product_chain`)

---

### 2. **stores**
Physical store locations for each chain.

**Primary Key:** `id` (UUID)
**Unique Constraint:** `(chain, url)`

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | NOT NULL | Primary key |
| name | VARCHAR(255) | NOT NULL | Store name |
| chain | VARCHAR(64) | NOT NULL | Chain identifier |
| lat | DOUBLE | NOT NULL | Latitude coordinate |
| lon | DOUBLE | NOT NULL | Longitude coordinate |
| geog | GEOGRAPHY(Point, 4326) | NULL | Generated geography point for spatial queries |
| address | VARCHAR(255) | NULL | Street address |
| region | VARCHAR(64) | NULL | Region/area |
| url | VARCHAR(255) | NULL | Store-specific URL |
| created_at | TIMESTAMP | NOT NULL | Record creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `(chain, name)` (`uq_store_chain_name`)
- UNIQUE on `(chain, api_id)` (`uq_store_chain_api_id`)
- BTREE on `chain` (`ix_store_chain`)
- GiST on `geog` (spatial index for radius queries)

---

### 3. **prices**
Store-specific pricing for products (many-to-many relationship).

**Primary Key:** `id` (UUID)
**Foreign Keys:**
- `product_id` → `products.id`
- `store_id` → `stores.id`

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | NOT NULL | Primary key |
| product_id | UUID | NOT NULL | FK to products table |
| store_id | UUID | NOT NULL | FK to stores table |
| currency | VARCHAR(3) | NOT NULL | Currency code (default: NZD) |
| price_nzd | DOUBLE | NOT NULL | Regular price in NZD |
| promo_price_nzd | DOUBLE | NULL | Promotional price (if on sale) |
| promo_text | VARCHAR(255) | NULL | Promotion description |
| promo_ends_at | TIMESTAMP | NULL | Promotion end date |
| last_seen_at | TIMESTAMP | NOT NULL | Last time this price was observed |
| price_last_changed_at | TIMESTAMP | NOT NULL | When price last changed |
| is_member_only | BOOLEAN | NOT NULL | Members-only pricing flag |
| created_at | TIMESTAMP | NOT NULL | Record creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE on `(product_id, store_id)` (`uq_price_product_store`)
- BTREE on `product_id` (`ix_price_product_id` - FK index for JOINs)
- BTREE on `store_id` (`ix_price_store_id` - FK index for JOINs)
- BTREE on `price_nzd` (`ix_price_price_nzd`)
- BTREE on `promo_price_nzd` (`ix_price_promo_price_nzd`)
- BTREE on `price_last_changed_at` (`ix_price_last_changed`)
- BTREE on `last_seen_at` (`ix_price_last_seen`)

---

### 4. **ingestion_runs**
Tracks scraping job runs and their outcomes.

**Primary Key:** `id` (UUID)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | UUID | NOT NULL | Primary key |
| chain | VARCHAR(64) | NOT NULL | Chain identifier |
| status | VARCHAR(32) | NOT NULL | Run status (success, failed, etc.) |
| started_at | TIMESTAMP | NOT NULL | Run start time |
| finished_at | TIMESTAMP | NULL | Run completion time |
| items_total | INTEGER | NOT NULL | Total items processed |
| items_changed | INTEGER | NOT NULL | Items that changed |
| items_failed | INTEGER | NOT NULL | Items that failed |
| log_url | VARCHAR(255) | NULL | Link to detailed logs |
| created_at | TIMESTAMP | NOT NULL | Record creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

---

## Categories

### Available Categories (28 total)
Organized by parent category:

**Beer:**
- beer, lager, ipa, ale, stout, craft_beer

**Wine:**
- wine, red_wine, white_wine, rose, sparkling, champagne, fortified_wine

**Spirits:**
- vodka, gin, rum, whisky, bourbon, scotch, tequila, brandy, liqueur, soju

**Others:**
- rtd, cider, mixer, non_alcoholic, spirits

### Category Hierarchy
```
beer
├── lager
├── ipa
├── ale
├── stout
└── craft_beer

wine
├── red_wine
├── white_wine
├── rose
├── sparkling
├── champagne
└── fortified_wine

whisky
├── bourbon
└── scotch
```

---

## Key Constraints & Business Rules

1. **Unique Products:** Each product is unique per (chain, source_product_id)
2. **Unique Stores:** Each store is unique per (chain, url)
3. **Price Tracking:** Prices track historical changes via `price_last_changed_at`
4. **Multi-Store Support:** Same product can have different prices at different stores
5. **Automatic Timestamps:** All tables auto-update `updated_at` on modification

---

## Performance Considerations

### How Indexes Improve Database Performance

Without indexes, PostgreSQL must perform a **sequential scan** — reading every row in a table to find matches. As the dataset grows (currently ~20k price rows and ~10k products), this becomes increasingly expensive. Indexes create sorted B-tree structures that let the database jump directly to matching rows, reducing query time from O(n) to O(log n).

Below is each index, the queries it accelerates, and why it matters.

---

### stores indexes

| Index | Columns | Query Pattern | Performance Impact |
|-------|---------|---------------|-------------------|
| `uq_store_chain_name` | `(chain, name)` UNIQUE | Scraper upserts: find-or-create a store by chain + name | Prevents full table scan on every scraped store. Also enforces no duplicate stores per chain. |
| `uq_store_chain_api_id` | `(chain, api_id)` UNIQUE | Scraper upserts for API-sourced stores (PAK'nSAVE, New World) | Same as above for stores identified by API ID rather than name. |
| `ix_store_chain` | `chain` | `sweep_chain_promos()` subquery: `SELECT id FROM stores WHERE chain = ?`; chain filter in `fetch_products()` | Narrows the store set quickly when filtering by chain. Without it, the subquery inside the freshness sweep would scan all stores. |
| GiST on `geog` | `geog` (spatial) | `ST_DWithin(geog, user_point, radius)` in `_get_store_ids_within_radius()` | PostGIS spatial index enables radius queries in O(log n) instead of computing distance to every store. Critical for the location-based search flow. |

---

### products indexes

| Index | Columns | Query Pattern | Performance Impact |
|-------|---------|---------------|-------------------|
| `uq_product_source` | `(chain, source_product_id)` UNIQUE | Scraper upserts: find-or-create a product by chain + source ID | Avoids full table scan on every scraped product (~10k rows). Also the deduplication constraint. |
| `ix_product_chain` | `chain` | `Product.chain.in_(params.chain)` filter in `fetch_products()` | When a user filters by chain (e.g. "liquorland"), the planner uses this index to skip products from other chains entirely. |

---

### prices indexes

The prices table is the largest (~20k rows) and the most heavily queried, so its indexes have the biggest impact.

| Index | Columns | Query Pattern | Performance Impact |
|-------|---------|---------------|-------------------|
| `uq_price_product_store` | `(product_id, store_id)` UNIQUE | Scraper upserts: find-or-create a price row for a product at a store | Prevents full table scan during every price upsert. Also the deduplication constraint. |
| `ix_price_product_id` | `product_id` | `JOIN Price ON Price.product_id = Product.id` in every search query and product detail view | **FK index for JOINs.** PostgreSQL does not auto-index foreign keys. Without this, every JOIN from products to prices would sequential-scan the entire prices table. |
| `ix_price_store_id` | `store_id` | `JOIN Store ON Store.id = Price.store_id`; `Price.store_id == store_id` in `sweep_store_promos()` | **FK index for JOINs.** Same reasoning — makes the prices-to-stores join efficient. Also speeds up per-store freshness sweeps. |
| `ix_price_price_nzd` | `price_nzd` | `effective_price >= params.price_min` / `<= params.price_max` range filters; `ORDER BY total_price` sort | Enables index range scans for price-bound queries instead of scanning + sorting all rows. |
| `ix_price_promo_price_nzd` | `promo_price_nzd` | `promo_price_nzd IS NOT NULL` filter when `promo_only=True`; promo expiry cleanup | Quickly identifies rows that have active promotions. The majority of rows have NULL promo prices, so partial index lookups skip most of the table. |
| `ix_price_last_changed` | `price_last_changed_at` | `ORDER BY price_last_changed_at DESC` (the "newest" sort); tie-breaker in all sort modes | Avoids a full-table sort when users browse by "newest". Also used as a secondary sort in every query. |
| `ix_price_last_seen` | `last_seen_at` | `Price.last_seen_at < run_started_at` in `sweep_chain_promos()` / `sweep_store_promos()`; staleness checks | Lets freshness sweeps efficiently find stale rows. Without it, every sweep after a scrape run would scan all prices. |

---

### ingestion_runs indexes

| Index | Columns | Query Pattern | Performance Impact |
|-------|---------|---------------|-------------------|
| `ix_ingestion_run_chain_status` | `(chain, status)` | Querying run status per chain (e.g. "latest completed run for liquorland") | Composite index satisfies both the chain filter and status filter in a single lookup. |
| `ix_ingestion_run_chain_started` | `(chain, started_at)` | Finding the most recent run for a chain (`ORDER BY started_at DESC LIMIT 1`) | The composite index lets PostgreSQL do an index-only backward scan — no sort step needed. |

---

### Summary: Key Performance Wins

1. **JOIN acceleration** (`ix_price_product_id`, `ix_price_store_id`): Every product search does a 3-way `Product -> Price -> Store` join. Without FK indexes, each join would be a nested-loop over the full prices table — O(n * m) instead of O(n * log m).

2. **Spatial queries** (GiST on `geog`): The location-based "stores within X km" query uses `ST_DWithin`, which is only fast with a spatial index. Without it, PostgreSQL computes haversine distance to every store.

3. **Scraper upserts** (unique constraints): Scrapers run repeatedly, upserting thousands of rows per run. The unique indexes turn each "does this row exist?" check from a full scan into a B-tree probe.

4. **Freshness sweeps** (`ix_price_last_seen`, `ix_price_store_id`): After each scrape, stale promos are cleared via `WHERE last_seen_at < run_start AND store_id IN (...)`. Both columns are indexed, so the sweep touches only the relevant rows.

5. **Sort avoidance** (`ix_price_last_changed`, `ix_price_price_nzd`): When sorting by "newest" or "total_price", PostgreSQL can read rows in index order rather than sorting the full result set in memory.

### Query Patterns
- **Product search:** Filter by `products.name`, `products.brand`, `products.category`
- **Price comparison:** JOIN products -> prices -> stores, filter by location
- **Deal finding:** Filter by `prices.promo_price_nzd IS NOT NULL`
- **Category browsing:** Filter by `products.category` with hierarchy support

---

## Data Quality Metrics

### Liquor Centre (Primary Chain)
- ✅ **87.6% categorized** (7,769 of 8,868 products)
- ✅ **100% brand inference** (all products have brand)
- ✅ **~95% volume parsing** (most products have volume data)
- ✅ **~70% ABV extraction** (from product names)

### Other Chains
- Super Liquor: ~82.8% categorized
- Liquorland: ~86.9% categorized
- Bottle-O: Uses source categories
- Countdown: Limited sample data
