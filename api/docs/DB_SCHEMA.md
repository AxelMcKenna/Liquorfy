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
- UNIQUE on `(chain, url)` (added to prevent duplicates)

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
- BTREE on `price_last_changed_at` (for tracking price changes)
- BTREE on `price_nzd` (for price queries)
- BTREE on `promo_price_nzd` (for promo queries)

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

### Indexed Fields
- `prices.price_nzd` - For price range queries
- `prices.promo_price_nzd` - For finding deals
- `prices.price_last_changed_at` - For tracking price changes
- `products.(chain, source_product_id)` - For upsert operations
- `stores.(chain, url)` - For preventing duplicates

### Query Patterns
- **Product search:** Filter by `products.name`, `products.brand`, `products.category`
- **Price comparison:** JOIN products → prices → stores, filter by location
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
