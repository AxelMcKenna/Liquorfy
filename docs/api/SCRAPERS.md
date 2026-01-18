# Liquorfy Scrapers Documentation

Comprehensive documentation for all 10 liquor chain scrapers in the Liquorfy platform.

## Overview

Liquorfy scrapes product and pricing data from 10 major liquor retailers in New Zealand. The scrapers use two primary approaches:

1. **API-Based Scrapers** (5/10) - Fast, reliable, direct API calls
2. **HTML-Based Scrapers** (5/10) - Browser automation with HTML parsing

---

## Scraper Status Summary

| Chain | Type | Status | Products Tested | Store Coverage | Notes |
|-------|------|--------|-----------------|----------------|-------|
| **Countdown** | API | ✅ Working | 26 | All NZ stores (~180) | Chain-wide pricing |
| **New World** | API | ✅ Working | 336 | All stores (144) | Store-specific pricing |
| **PakNSave** | API | ✅ Working | 364 | All stores (57) | Store-specific pricing |
| **Liquorland** | HTML | ✅ Working | - | All NZ stores (~100) | Chain-wide pricing |
| **Liquor Centre** | HTML | ✅ Working | 48 | All stores (90) | Store-specific pricing |
| **Super Liquor** | HTML | ✅ Working | - | All NZ stores (~130) | Chain-wide pricing |
| **Bottle O** | HTML | ✅ Working | 48 | All NZ stores (~40) | Chain-wide pricing |
| **Glengarry** | HTML | ✅ Working | 129 | Flagship stores (3-5) | Limited locations |
| **Thirsty Liquor** | API | ✅ Working | 219 | All NZ stores (130+) | Chain-wide pricing, Shopify |
| **Black Bull** | API | ✅ Working | 96 | 3 stores (of 60+) | **LIMITED: 5% coverage**, Shopify |

**Overall**: 10/10 scrapers operational ✅

---

## API-Based Scrapers

### 1. Countdown (CountdownAPIScraper)

**File**: `app/scrapers/countdown_api.py`

#### Store Coverage

- **Geographic Coverage**: All Countdown stores nationwide (~180 stores)
- **Pricing Model**: Chain-wide pricing (same price at all stores)
- **Store Types**: Supermarkets (Countdown brand, owned by Woolworths NZ)
- **Capability**: Scrapes complete national catalog, single API call covers all stores

#### How It Works

Countdown uses the Woolworths NZ public API which powers their website.

**API Endpoint**: `https://www.woolworths.co.nz/api/v1/products`

**Request Method**: GET with query parameters

**Authentication**: Session cookies only (no API key required)

#### Key Features

- **Category Filtering**: Uses `dasFilter` URL parameters
  ```
  dasFilter=Department;;beer-cider-wine;false
  dasFilter=Aisle;;beer;false
  ```
- **Critical Headers**:
  - `x-requested-with: OnlineShopping.WebApp` (required!)
  - `referer: https://www.woolworths.co.nz/shop/browse/{category}/{aisle}`

#### Categories Scraped

```python
categories = [
    ("beer-cider-wine", "beer"),
    ("beer-cider-wine", "cider"),
    ("beer-cider-wine", "red-wine"),
    ("beer-cider-wine", "white-wine"),
    ("beer-cider-wine", "rose-wine"),
    ("beer-cider-wine", "sparkling-wine"),
    ("beer-cider-wine", "premix-rtd"),
]
```

#### Response Structure

```json
{
  "products": {
    "items": [
      {
        "sku": "12345",
        "name": "Product Name",
        "brand": "Brand Name",
        "variety": "Variety",
        "price": {
          "originalPrice": 19.99,
          "salePrice": 15.99,
          "isSpecial": true,
          "savePrice": 4.00,
          "isClubPrice": false
        },
        "size": {
          "volumeSize": "24 x 330mL"
        },
        "images": {
          "big": "https://...",
          "small": "https://..."
        },
        "slug": "product-slug"
      }
    ],
    "totalItems": 26
  }
}
```

#### Cookie Acquisition

Uses Playwright to visit homepage and capture session cookies:

```python
async def _get_cookies(self) -> dict:
    # Open browser to Countdown homepage
    # Wait for cookies to be set
    # Extract and return cookie dictionary
```

#### Advantages

- ✅ Fast (direct API calls)
- ✅ Reliable (official API)
- ✅ Structured data
- ✅ No HTML parsing needed

#### Limitations

- ⚠️ Requires session cookies refresh
- ⚠️ API may change without notice

---

### 2. New World (NewWorldAPIScraper)

**File**: `app/scrapers/new_world_api.py`

#### Store Coverage

- **Geographic Coverage**: All stores nationwide (144 stores)
- **Total Stores**: 144 New World stores
- **Pricing Model**: Store-specific pricing (prices vary by location)
- **Data Source**: `/app/data/newworld_stores.json`
- **Default Behavior**: Scrapes all 144 stores by default (`scrape_all_stores=True`)
- **Capability**:
  - ✅ Scrapes all 144 stores automatically
  - ✅ Can scrape single store for testing (`scrape_all_stores=False`)
  - ✅ Captures store-specific pricing for all locations
- **Store Selection**: Set `scrape_all_stores=False` to use single default store

#### How It Works

New World uses the Foodstuffs NZ internal API (same infrastructure as PakNSave).

**API Endpoint**: `https://api-prod.newworld.co.nz/v1/edge/search/paginated/products`

**Request Method**: POST with JSON body

**Authentication**: JWT Bearer token + session cookies

#### Key Features

- **Algolia-Style Search**: Uses search query format
- **Pagination**: Supports paginated results
- **Store-Specific**: Requires store ID for pricing

#### Request Structure

```python
payload = {
    "storeId": "9629ea6d-aaf5-4076-8c65-11cc859d7cfe",  # Royal Oak Auckland
    "query": category,
    "searchType": "browse",
    "size": 120,
    "start": 0,
    "facetFilters": [[f"productCategory:{category}"]],
    "analytics": True,
}

headers = {
    "authorization": f"Bearer {token}",
    "content-type": "application/json",
}
```

#### Categories Scraped

```python
categories = [
    "Beer, Wine & Cider > Beer",
    "Beer, Wine & Cider > Craft Beer",
    "Beer, Wine & Cider > Cider",
    "Beer, Wine & Cider > Red Wine",
    "Beer, Wine & Cider > White Wine",
    "Beer, Wine & Cider > Rosé Wine",
    "Beer, Wine & Cider > Champagne & Sparkling Wine",
    "Beer, Wine & Cider > Seltzers & Other Alcoholic Drinks",
]
```

#### Response Structure

```json
{
  "products": [
    {
      "sku": "5000213101131",
      "name": "Stella Artois Premium Lager 12pk Bottles 330ml",
      "brand": "Stella Artois",
      "displayName": "Stella Artois Premium Lager",
      "price": {
        "originalPrice": 25.00,
        "salePrice": 22.00
      },
      "size": "12x330ml",
      "images": ["https://..."]
    }
  ],
  "pagination": {
    "totalCount": 336
  }
}
```

#### Token Acquisition

Uses Playwright with stealth mode to obtain JWT token:

```python
async def _get_auth_token(self) -> tuple[str, dict]:
    # Open browser to New World
    # Extract JWT from localStorage: __nw_access_token__
    # Extract session cookies
    # Return (token, cookies)
```

#### Advantages

- ✅ Fastest scraper (336 products in seconds)
- ✅ Comprehensive product data
- ✅ Official API with structured responses
- ✅ Supports pagination

---

### 3. PakNSave (PakNSaveAPIScraper)

**File**: `app/scrapers/paknsave_api.py`

#### Store Coverage

- **Geographic Coverage**: All stores nationwide (57 stores)
- **Total Stores**: 57 PakNSave stores
- **Pricing Model**: Store-specific pricing (prices vary by location)
- **Data Source**: `/app/data/paknsave_stores.json`
- **Default Behavior**: Scrapes all 57 stores by default (`scrape_all_stores=True`)
- **Capability**:
  - ✅ Scrapes all 57 stores automatically
  - ✅ Can scrape single store for testing (`scrape_all_stores=False`)
  - ✅ Captures store-specific pricing for all locations
- **Store Selection**: Set `scrape_all_stores=False` to use single default store

#### How It Works

Identical to New World (same Foodstuffs infrastructure).

**API Endpoint**: `https://api-prod.paknsave.co.nz/v1/edge/search/paginated/products`

**Request Method**: POST with JSON body

**Authentication**: JWT Bearer token + session cookies

#### Key Differences from New World

1. **Domain**: `paknsave.co.nz` instead of `newworld.co.nz`
2. **Default Store**: Different store ID
3. **Branding**: PakNSave-specific assets

#### Categories Scraped

Same as New World (8 categories in "Beer, Wine & Cider" department)

#### Token Acquisition

```python
async def _get_auth_token(self) -> tuple[str, dict]:
    # Visit https://www.paknsave.co.nz
    # Extract JWT from localStorage: __ps_access_token__
    # Return (token, cookies)
```

#### Test Results

- ✅ 364 products scraped from test run
- ✅ All categories working
- ✅ Pricing and promotions captured

---

### 4. Thirsty Liquor (ThirstyLiquorScraper)

**File**: `app/scrapers/thirsty_liquor.py`

#### Store Coverage

- **Geographic Coverage**: All stores nationwide (130+ stores)
- **Total Stores**: 130+ Thirsty Liquor stores
- **Pricing Model**: Chain-wide pricing (same price at all stores)
- **Platform**: Shopify-based e-commerce
- **Default Behavior**: Scrapes complete national catalog
- **Capability**:
  - ✅ Scrapes all products via Shopify API
  - ✅ Chain-wide pricing covers all 130+ locations
  - ✅ No store-specific configuration needed

#### How It Works

Thirsty Liquor uses Shopify's standard JSON API for product data.

**API Endpoint**: `https://thirstyliquor.co.nz/collections/{collection}/products.json`

**Request Method**: GET with query parameters

**Authentication**: None required (public API)

**Pagination**: Standard Shopify pagination (limit=250, page={n})

#### Categories Scraped

5 product collections:
- Beer
- Wine
- Spirits
- Cider
- RTDs (Ready-to-Drink)

#### Response Format

```json
{
  "products": [
    {
      "id": 10339604922662,
      "title": "Tuatara Brightside Bright IPA 6pk Cans",
      "vendor": "Tuatara",
      "handle": "tuatara-brightside-bright-ipa-6pk-cans",
      "variants": [
        {
          "price": "25.99",
          "compare_at_price": null,
          "available": true
        }
      ],
      "images": [{"src": "https://cdn.shopify.com/..."}]
    }
  ]
}
```

#### Promotion Detection

Shopify provides sale detection through `compare_at_price`:
- If `compare_at_price` > `price`: Product is on sale
- `price` = sale price
- `compare_at_price` = original price

#### Advantages

- ✅ Fastest scraper (pure API, no browser)
- ✅ No authentication required
- ✅ Standard Shopify format
- ✅ Reliable and stable
- ✅ Comprehensive product data
- ✅ Built-in image URLs

#### Test Results

- ✅ 219 beer products scraped in test run
- ✅ ~1000+ total products across all categories
- ✅ Promotion detection working (compare_at_price)
- ✅ All product metadata captured

---

### 5. Black Bull (BlackBullScraper)

**File**: `app/scrapers/black_bull.py`

⚠️ **LIMITED COVERAGE WARNING**: This scraper only covers **3 out of 60+ stores** (~5% coverage)

#### Store Coverage

- **Geographic Coverage**: 3 franchise stores with Shopify e-commerce
- **Total Black Bull Stores in NZ**: 60+ franchise locations
- **Stores Scraped**: 3 stores (5% coverage)
  - Porirua: `blackbullporirua.co.nz`
  - Greenwood (Hamilton): `blackbullliquorgreenwood.co.nz`
  - Hornby Hub (Christchurch): `blackbullliquorhornbyhub.co.nz`
- **Pricing Model**: Store-specific (each franchise independently operated)
- **Platform**: Shopify-based e-commerce
- **Franchise Model**: Black Bull operates as independent franchises, not a corporate chain

#### How It Works

Black Bull stores that offer online ordering use Shopify's standard JSON API.

**API Endpoint**: `https://{store-domain}/collections/{collection}/products.json`
**Request Method**: GET with query parameters
**Authentication**: None required (public API)
**Pagination**: Standard Shopify pagination (limit=250, page={n})

The scraper iterates through 3 known Shopify stores, fetching products from each independently.

#### Collections Scraped

```python
collections = [
    "beer-cider",
    "wine",
    "spirits",
    "rtds",
    "liqueurs",
    "mixers",
]
```

#### Promotion Detection

Uses Shopify's `compare_at_price` field:
- If `compare_at_price` > `price`: Product is on sale
- `price` = sale price
- `compare_at_price` = original price

#### Stores NOT Covered (57+ locations)

⚠️ **The following Black Bull stores do NOT have online ordering** and are not included in this scraper:

**Auckland Region (17 stores without online ordering):**
- Clendon, Everglade Dr, Flat Bush, Grey Lynn, Hillcrest, Kaitaia, Kaukapakapa, Kohimarama, Manurewa, Mt Eden Village, Mt Richmond, Northcote, Norwest (Kumeu), Panmure, Queen Street, Royal Oak, Russel Rd, Sky Liquor (Papatoetoe), Somerville, Taipa

**Waikato Region (13 stores without online ordering):**
- Avalon, Bull Ring Taupo, Cambridge, Fairfield, Grasslands Place, Huntly, Matamata, Morrinsville, Ohaupo Rd, Peachgrove Road, Putaruru, Te Kuiti, Thames

**Bay of Plenty - Hawkes Bay (2 stores):**
- Karamu Rd (Hastings), Napier

**Gisborne (1 store):**
- Gisborne

**Manawatu - Wanganui (8 stores):**
- Foxton, Levin, Main Street (Palmerston North), Manaia, Ohakune, Shannon, Waiouru
- Note: Hawera has online ordering but uses DNN/Hotcakes platform (not Shopify), not covered by this scraper

**Taranaki (4 stores):**
- Eltham, Glover Rd, Opunake, Stratford

**Wellington (3 stores without online ordering):**
- Paraparaumu, Petone, Whitby
- Note: Porirua IS covered (Shopify)

**South Island (1 store without online ordering):**
- The Peg (Belfast, Christchurch)
- Note: Hornby Hub IS covered (Shopify)

**Why Limited Coverage?**
1. **Franchise model**: Each Black Bull is independently operated
2. **No unified e-commerce**: No corporate online ordering system
3. **Platform fragmentation**: Stores use different platforms (Shopify, DNN, or none)
4. **Most stores physical-only**: 57+ stores don't offer online ordering

#### Test Results

- ✅ 96 beer/cider products scraped from Porirua in test run
- ✅ Store context properly attached to each product
- ✅ Promotion detection working (compare_at_price)
- ✅ All 3 Shopify stores accessible
- ⚠️ Only 3 stores covered (5% of Black Bull network)

---

## HTML-Based Scrapers

### 6. Liquorland (LiquorlandScraper)

**File**: `app/scrapers/liquorland.py`

#### Store Coverage

- **Geographic Coverage**: All Liquorland stores nationwide (~100 stores)
- **Pricing Model**: Chain-wide pricing (same price at all stores)
- **Store Types**: Liquorland franchise stores (owned by Foodstuffs)
- **Capability**:
  - ✅ Scrapes complete national catalog
  - ✅ Single scrape covers all stores
  - ✅ No store-specific configuration needed
- **Locations**: Major cities and towns across NZ (North and South Island)

#### How It Works

Liquorland uses **Vue.js 3** with server-side rendering + client-side hydration. Products are embedded in the initial HTML and Vue makes them interactive.

**Technology Stack**:
- Vue.js 3.5.20 (compatibility mode)
- Axios for API calls
- Server-side rendering (SSR)

**Why HTML Scraping?**
- No product API available
- Products embedded in initial HTML response (210KB)
- Vue renders them client-side (grows to 305KB after JS)

#### Rendering Process

1. Server sends HTML with embedded product data
2. Browser loads Vue.js
3. Vue hydrates the DOM (makes interactive)
4. No separate product API calls needed

#### Scraping Approach

Uses **Playwright** to:
1. Load category pages with full JavaScript execution
2. Wait for Vue to render products
3. Extract final rendered HTML
4. Parse product elements

#### Categories Scraped

```python
catalog_urls = [
    "https://www.liquorland.co.nz/beer",
    "https://www.liquorland.co.nz/craft-beer",
    "https://www.liquorland.co.nz/cider",
    "https://www.liquorland.co.nz/wine",
    "https://www.liquorland.co.nz/wine/red",
    "https://www.liquorland.co.nz/wine/white",
    "https://www.liquorland.co.nz/wine/rose",
    "https://www.liquorland.co.nz/wine/sparkling",
    "https://www.liquorland.co.nz/spirits",
    "https://www.liquorland.co.nz/spirits/whisky",
    "https://www.liquorland.co.nz/spirits/gin",
    "https://www.liquorland.co.nz/spirits/vodka",
    "https://www.liquorland.co.nz/spirits/rum",
    "https://www.liquorland.co.nz/rtd",
]
```

#### HTML Structure

Products are rendered as interactive Vue components with specific class names and data attributes.

#### Rate Limiting

```python
DELAY_BETWEEN_REQUESTS = 1.0  # seconds between pages
DELAY_BETWEEN_CATEGORIES = 2.5  # seconds between categories
```

#### User Agent

```python
user_agent = "Liquorfy/1.0 (Price Comparison Bot; +https://liquorfy.co.nz)"
```

Respectful bot identification per robots.txt compliance.

---

### 7. Liquor Centre (LiquorCentreScraper)

**File**: `app/scrapers/liquor_centre.py`

#### Store Coverage

- **Geographic Coverage**: All stores nationwide (90 stores)
- **Total Stores**: 90 Liquor Centre stores
- **Pricing Model**: Store-specific pricing (prices vary by location)
- **Data Source**: `/app/data/liquor_centre_stores.json`
- **Default Behavior**: Scrapes all 90 stores by default (`scrape_all_stores=True`)
- **Capability**:
  - ✅ Scrapes all 90 stores automatically
  - ✅ Can scrape subset of stores for testing (pass custom `stores` list)
  - ✅ Can use 7 representative stores (`scrape_all_stores=False`)
  - ✅ Captures store-specific pricing for all locations
  - ℹ️ Full scrape: 5 categories × 90 stores = 450 scrapes
- **Store Selection**:
  - All stores: `LiquorCentreScraper(scrape_all_stores=True)` (default)
  - Subset: `LiquorCentreScraper(scrape_all_stores=False)` (7 stores)
  - Custom: `LiquorCentreScraper(stores=["royal-oak", "milford"])`
- **Scaling**: Each store is independent, suitable for parallel execution

#### How It Works

Liquor Centre operates with **store-specific subdomains** and per-store pricing.

**Domain Structure**: `{store-slug}.shop.liquor-centre.co.nz`

**Why HTML Scraping?**
- No product API
- Server-side rendered HTML
- Store-specific pricing requires multiple stores

#### Multi-Store Architecture

Each of 90+ stores has a unique subdomain:
- `beerescourt.shop.liquor-centre.co.nz` (Hamilton)
- `royal-oak.shop.liquor-centre.co.nz` (Auckland)
- `milford.shop.liquor-centre.co.nz` (Auckland North Shore)
- etc.

#### Default Stores Scraped

Representative sample from different regions:

```python
DEFAULT_STORES = [
    "beerescourt",  # Hamilton
    "greenhithe",   # Auckland North
    "milford",      # Auckland North Shore
    "st-lukes",     # Auckland Central
    "pakuranga",    # Auckland East
    "royal-oak",    # Auckland South
    "opawa",        # Christchurch
]
```

#### Categories Scraped

```python
CATEGORIES = ["beer", "wine", "spirits", "cider", "rtds"]
```

#### URL Construction

```python
def _build_url(store_slug: str, category: str, page: int = 1) -> str:
    base_url = f"https://{store_slug}.shop.liquor-centre.co.nz/category/{category}"
    if page > 1:
        return f"{base_url}?page={page}"
    return base_url
```

#### Pagination

Supports automatic pagination:
- Looks for `a[rel="next"]` link
- Continues until no next page
- Safety limit: 50 pages per category

#### HTML Structure

Uses `.talker` class for product cards:
- `.talker__name` - Product name
- `.talker__price` - Current price
- `.talker__sticker` - Promotional badges
- `.talker__image` - Product image

#### Store-Specific Pricing

Each store can have different prices for the same product. The scraper:
1. Tags HTML with store metadata
2. Associates prices with specific stores in database
3. Enables location-based price comparison

#### Test Results

- ✅ 48 products from royal-oak store
- ✅ 22 pages fetched across 5 categories
- ✅ Promotions and pricing captured

---

### 8. Super Liquor (SuperLiquorScraper)

**File**: `app/scrapers/super_liquor.py`

#### Store Coverage

- **Geographic Coverage**: All Super Liquor stores nationwide (~130 stores)
- **Pricing Model**: Chain-wide pricing (same price at all stores)
- **Store Types**: Independently owned franchises under Super Liquor brand
- **Capability**:
  - ✅ Scrapes complete national catalog
  - ✅ Single scrape covers all stores
  - ✅ No store-specific configuration needed
- **Locations**: Extensive coverage including smaller towns and regional centers
- **Network**: Largest liquor franchise network in NZ by store count

#### How It Works

Super Liquor uses traditional **server-side HTML rendering**. Products are in the HTML when the page loads.

**Why HTML Scraping?**
- No product API
- Products fully rendered on server
- JavaScript only enhances UI (not required for data)

#### Technology

Traditional server-rendered pages (likely PHP or similar backend)

#### Scraping Approach

Uses **Playwright** but could work with simple HTTP client:
1. Fetch category pages
2. Parse HTML directly
3. Extract product data from HTML structure

#### Categories Scraped

Similar to other chains:
- Beer
- Wine (Red, White, Rosé, Sparkling)
- Spirits
- Cider
- RTDs

#### HTML Structure

Server-rendered product cards with specific class patterns (varies by page template)

---

### 9. Bottle O (BottleOScraper)

**File**: `app/scrapers/bottle_o.py`

#### Store Coverage

- **Geographic Coverage**: All Bottle O stores nationwide (~40 stores)
- **Pricing Model**: Chain-wide pricing (same price at all stores)
- **Store Types**: Owned by Tasman Liquor Company (part of Lion NZ)
- **Capability**:
  - ✅ Scrapes complete national catalog
  - ✅ Single scrape covers all stores
  - ✅ No store-specific configuration needed
- **Locations**: Major urban centers (Auckland, Wellington, Christchurch, Hamilton)
- **Network**: Smaller chain focused on metropolitan areas

#### How It Works

Bottle O uses a **unique approach**: extracting data from Google Tag Manager's `dataLayer`.

**Why GTM dataLayer?**
- Site uses GTM for analytics
- GTM dataLayer contains structured product data
- More reliable than HTML parsing

#### GTM DataLayer Structure

```javascript
window.gtmDataLayer = [
  {
    "event": "productListImpression",
    "ecommerce": {
      "impressions": [
        {
          "id": "08008440519641",
          "name": "Asahi 12x330ml Cans",
          "price": "25.99",
          "brand": "Asahi",
          "category": "Beer",
          "position": 1
        }
      ]
    }
  }
]
```

#### Scraping Process

1. **Load Page**: Use Playwright to load category page
2. **Wait for GTM**: Let JavaScript populate `window.gtmDataLayer`
3. **Extract Data**: Read GTM dataLayer via JavaScript evaluation
4. **Parse Products**: Extract from `productListImpression` events
5. **Match Images**: Cross-reference with HTML for product images

#### Dual Extraction

The scraper extracts **both**:
1. **GTM dataLayer** (structured product data)
2. **HTML** (for product images)

Combined in parse phase:

```python
combined_data = {
    "gtm": json.loads(gtm_data),
    "html": html
}
```

#### Search URLs

Uses search interface for category filtering:

```python
catalog_urls = [
    "https://thebottleo.co.nz/search?q[]=category:beer&sort_by=top_products",
    "https://thebottleo.co.nz/search?q[]=category:wine&sort_by=top_products",
    "https://thebottleo.co.nz/search?q[]=category:spirits&sort_by=top_products",
    "https://thebottleo.co.nz/search?q[]=category:rtd&sort_by=top_products",
    "https://thebottleo.co.nz/search?q[]=category:cider&sort_by=top_products",
]
```

#### Image Extraction

Images are extracted from HTML using name matching:

1. Normalize product names from GTM and HTML
2. Match by name (fuzzy matching with/without volume)
3. Associate image URLs with products

```python
def _normalize_name(name: str) -> str:
    # Lowercase, remove extra spaces
    # Normalize volume format: "12 x 330ml" -> "12x330ml"
    return normalized
```

#### GTM Event Filtering

Only processes `productListImpression` events:

```python
for event in gtm_data:
    if event.get('event') == 'productListImpression':
        impressions = event.get('ecommerce', {}).get('impressions', [])
        # Parse each impression
```

#### Advantages

- ✅ Structured data (more reliable than HTML)
- ✅ GTM format is stable (rarely changes)
- ✅ Includes analytics metadata
- ✅ Less affected by HTML/CSS changes

#### Test Results

- ✅ 48 products from beer category
- ✅ All product data including images
- ✅ GTM dataLayer extraction working perfectly

---

### 10. Glengarry (GlengarryScraper)

**File**: `app/scrapers/glengarry.py`

#### Store Coverage

- **Geographic Coverage**: Flagship stores only (3-5 locations)
- **Total Stores**:
  - Victoria Park (Auckland) - Flagship
  - Thorndon (Wellington) - Flagship
  - Limited additional locations
- **Pricing Model**: Chain-wide pricing (same across all stores)
- **Store Type**: Specialty wine & spirits retailer (premium/boutique)
- **Capability**:
  - ✅ Scrapes complete catalog
  - ✅ Single scrape covers all stores
  - ⚠️ Limited physical locations (online-focused)
- **Focus**: Premium wines, craft spirits, boutique selections
- **Online**: Strong online presence, delivers nationwide

**Note**: Glengarry is not a large retail chain but a specialty merchant with extensive online catalog. Physical stores are limited, but product range is comprehensive.

#### How It Works

Glengarry uses **legacy JSP (JavaServer Pages)** technology for server-side rendering.

**Why HTML Scraping?**
- No product API
- Legacy technology stack (2000s-era JSP)
- Products fully rendered on server

#### Technology Stack

- **JSP**: JavaServer Pages
- **Domain**: `glengarrywines.co.nz` (note: not `glengarry.co.nz`)
- **Server-side**: All rendering happens server-side

#### Scraping Approach

Uses **Playwright** to:
1. Load category pages
2. Wait for `.productDisplaySlot` elements
3. Parse server-rendered HTML

#### Categories Scraped

```python
catalog_urls = [
    "https://www.glengarrywines.co.nz/beer",
    "https://www.glengarrywines.co.nz/wine/red",
    "https://www.glengarrywines.co.nz/wine/white",
    "https://www.glengarrywines.co.nz/wine/rose",
    "https://www.glengarrywines.co.nz/spirits/whisky",
    "https://www.glengarrywines.co.nz/spirits/gin",
    "https://www.glengarrywines.co.nz/spirits/vodka",
    "https://www.glengarrywines.co.nz/spirits/rum",
    "https://www.glengarrywines.co.nz/champagne",
    "https://www.glengarrywines.co.nz/specials",
]
```

#### HTML Structure

Glengarry-specific class names:

```html
<div class="productDisplaySlot">
  <div class="fontProductHead">
    <a href="/brands/garage-project">Garage Project</a>
  </div>
  <div class="fontProductHeadSub">
    <a href="/items/91118/garage+project+low+stakes+session+hazy">
      Low Stakes Session Hazy
    </a>
  </div>
  <div class="productDisplayPrice">
    <div class="fontProductPriceSub">WAS $3.99</div>
    <div class="fontProductPrice">NOW $2.99</div>
  </div>
  <img src="/images/v9/bottles/91118.png" class="productDisplayImage">
</div>
```

#### Key Selectors

- `.productDisplaySlot` - Product container
- `.fontProductHead a` - Brand name
- `.fontProductHeadSub a` - Product name + URL
- `.fontProductPriceSub` - WAS price
- `.fontProductPrice` - NOW price
- `img.productDisplayImage` - Product image

#### Sale Price Format

Unique "WAS/NOW" pricing:
- **WAS $3.99** - Original price
- **NOW $2.99** - Sale price

Parser extracts both and calculates savings.

#### Product ID Extraction

IDs extracted from URL pattern:
```
/items/91118/product-slug
       ^^^^^ - Product ID
```

Also validated against image URL:
```
/images/v9/bottles/91118.png
                    ^^^^^ - Should match
```

#### Robots.txt Compliance

Glengarry's robots.txt specifies:
```
Crawl-delay: 10
```

Scraper respects this through browser automation timing (natural page loads).

#### Test Results

- ✅ 129 products (beer + red wine categories)
- ✅ All sale prices captured correctly
- ✅ WAS/NOW pricing parsing working

---

## Common Scraping Patterns

### Base Scraper Class

All scrapers inherit from `Scraper` base class:

```python
class Scraper(ABC):
    chain: str  # Chain identifier

    @abstractmethod
    async def fetch_catalog_pages(self) -> List[str]:
        """Fetch raw data (HTML or JSON)"""
        pass

    @abstractmethod
    async def parse_products(self, payload: str) -> List[dict]:
        """Parse products from raw data"""
        pass

    async def run(self) -> IngestionRun:
        """Main execution: fetch, parse, persist to DB"""
        pass
```

### Database Integration

All scrapers use the same persistence layer:

```python
async def _upsert_product_and_prices(
    session: AsyncSession,
    product_data: dict,
    stores: List[Store]
) -> bool:
    # Upsert product
    # Upsert prices for each store
    # Track changes
```

### Product Data Format

Standardized product dictionary:

```python
{
    "chain": "countdown",
    "source_id": "12345",
    "name": "Product Name",
    "brand": "Brand Name",
    "category": "beer",
    "price_nzd": 19.99,
    "promo_price_nzd": 15.99,
    "promo_text": "Save $4.00",
    "promo_ends_at": datetime(...),
    "is_member_only": False,
    "pack_count": 24,
    "unit_volume_ml": 330,
    "total_volume_ml": 7920,
    "abv_percent": 5.0,
    "url": "https://...",
    "image_url": "https://...",
}
```

### Shared Utilities

#### Parser Utils (`app/services/parser_utils.py`)

```python
parse_volume(name: str) -> VolumeInfo  # Extract pack size and volume
extract_abv(name: str) -> float | None  # Extract ABV percentage
infer_brand(name: str) -> str  # Infer brand from product name
infer_category(name: str) -> str  # Categorize product
```

#### Promo Utils (`app/services/promo_utils.py`)

```python
parse_promo_price(text: str) -> float | None  # Extract promo price
parse_multi_buy_deal(text: str) -> dict | None  # Parse "2 for $X" deals
parse_promo_end_date(text: str) -> datetime | None  # Extract expiry
detect_member_only(text: str) -> bool  # Detect member-only deals
```

---

## Performance Comparison

### Speed Tests (Approximate)

| Scraper | Type | Time | Products | Speed |
|---------|------|------|----------|-------|
| **New World** | API | ~5s | 336 | 67 prod/s |
| **PakNSave** | API | ~6s | 364 | 61 prod/s |
| **Countdown** | API | ~8s | 26 | 3 prod/s |
| **Bottle O** | HTML/GTM | ~15s | 48 | 3 prod/s |
| **Liquor Centre** | HTML | ~45s | 48 (1 store) | 1 prod/s |
| **Glengarry** | HTML | ~30s | 129 (2 cats) | 4 prod/s |
| **Liquorland** | HTML | ~60s | ~200 | 3 prod/s |
| **Super Liquor** | HTML | ~60s | ~150 | 2.5 prod/s |

**API scrapers are 10-20x faster** than HTML scrapers.

---

## Error Handling

### Common Errors

#### 1. Bot Detection

**Symptom**: 403 Forbidden, Cloudflare challenges

**Solution**:
- Use undetected-playwright stealth mode
- Rotate user agents
- Respect rate limits
- Use session cookies

#### 2. SSL Certificate Errors

**Symptom**: `ERR_CERT_COMMON_NAME_INVALID`

**Solution**:
- Verify correct domain/subdomain
- Check store-specific URLs (Liquor Centre)
- Use correct protocol (https vs http)

#### 3. Timeout Errors

**Symptom**: `Page.goto: Timeout 60000ms exceeded`

**Solution**:
- Increase timeout
- Use `wait_until="domcontentloaded"` instead of `"networkidle"`
- Implement retry logic
- Handle gracefully and continue

#### 4. Missing Product Data

**Symptom**: Empty product lists, 0 products parsed

**Causes**:
- Age verification gates
- Changed HTML structure
- Missing JavaScript execution
- Wrong selectors

**Debugging**:
1. Save HTML to file
2. Check if products exist in HTML
3. Verify selectors match current structure
4. Check if JavaScript is executing

---

## Maintenance & Monitoring

### When APIs Change

**Countdown/New World/PakNSave**:
1. Monitor for HTTP errors (401, 403, 404)
2. Check if endpoint URLs changed
3. Verify request/response format
4. Update headers if needed

### When HTML Changes

**All HTML Scrapers**:
1. Run scraper, check product count
2. If 0 products: HTML structure changed
3. Save HTML and inspect manually
4. Update CSS selectors
5. Test parser with fixture data

### Monitoring Checklist

Daily checks:
- [ ] Run all scrapers
- [ ] Check products count > 0
- [ ] Verify prices are updating
- [ ] Check error rates in logs

Weekly checks:
- [ ] Compare product counts (trends)
- [ ] Verify new products detected
- [ ] Check promo detection accuracy
- [ ] Review failed items logs

### Adding New Stores

1. **Create scraper file** in `app/scrapers/`
2. **Inherit from `Scraper`** base class
3. **Implement required methods**:
   - `fetch_catalog_pages()`
   - `parse_products()`
4. **Register in registry**:
   ```python
   # app/scrapers/registry.py
   CHAINS = {
       "new_chain": NewChainScraper,
   }
   ```
5. **Add tests** and fixtures
6. **Document** in this file

---

## Best Practices

### 1. Respectful Scraping

- ✅ Identify your bot (user agent)
- ✅ Respect robots.txt
- ✅ Implement rate limiting
- ✅ Use reasonable delays
- ✅ Don't overwhelm servers
- ❌ Never use aggressive parallel requests

### 2. Data Quality

- ✅ Validate all parsed data
- ✅ Handle missing fields gracefully
- ✅ Normalize data formats
- ✅ Track parsing errors
- ✅ Log failed items for review

### 3. Error Resilience

- ✅ Expect failures (network, parsing, etc.)
- ✅ Continue on single item failures
- ✅ Retry transient errors
- ✅ Log errors with context
- ✅ Update run statistics

### 4. Performance

- ✅ Prefer API scrapers when available
- ✅ Use connection pooling
- ✅ Cache auth tokens/cookies
- ✅ Minimize page loads
- ✅ Parse incrementally

### 5. Maintainability

- ✅ Use clear selector names
- ✅ Document HTML structures
- ✅ Create fixture files
- ✅ Write integration tests
- ✅ Keep scrapers independent

---

## Troubleshooting Guide

### "No products found"

1. Check if page loads in browser
2. Verify selectors haven't changed
3. Check for age verification
4. Ensure JavaScript is executing (HTML scrapers)
5. Save HTML and inspect manually

### "SSL/Certificate errors"

1. Verify domain is correct
2. Check for subdomain requirements (Liquor Centre)
3. Use https:// not http://
4. Check if site is down

### "Authentication failed"

1. Refresh cookies/tokens
2. Check if API changed
3. Verify headers are correct
4. Try browser workflow manually

### "Prices are wrong"

1. Check promotion parsing logic
2. Verify currency extraction
3. Check for WAS/NOW price swaps
4. Validate against website manually

---

## Future Improvements

### Potential Enhancements

1. **Distributed Scraping**
   - Run scrapers in parallel
   - Use task queue (Celery/RQ)
   - Scale horizontally

2. **Smart Rate Limiting**
   - Adaptive delays based on response times
   - Backoff on errors
   - Per-domain rate limits

3. **Change Detection**
   - Alert when scrapers break
   - Automated HTML structure diffing
   - Slack/email notifications

4. **Data Enrichment**
   - Product matching across chains
   - Historical price tracking
   - Promotion trend analysis

5. **API Discovery Automation**
   - Automatically detect new APIs
   - Monitor network traffic
   - Suggest API migrations

---

## Geographic Coverage Summary

### National Coverage (Store Location Database - Updated January 1, 2026)

| Chain | Stores in NZ | DB Coverage | Scraper Status | Coverage % |
|-------|--------------|-------------|----------------|------------|
| **Liquorland** | ~100 | ✅ 167 stores | Working | 167%* |
| **Super Liquor** | ~130 | ✅ 131 stores | Working | 101% |
| **Countdown** | ~180 | ❌ 0 stores | Failed (HTTP/2 error) | 0% |
| **New World** | 144 | ❌ 0 stores | Failed (DOM extraction) | 0% |
| **PakNSave** | 57 | ❌ 0 stores | Failed (DOM extraction) | 0% |
| **Liquor Centre** | 90 | ❌ 0 stores | Failed (DOM extraction) | 0% |
| **Thirsty Liquor** | 130+ | ⚠️ 11 stores | Partial (unknown issue) | 8% |
| **Bottle O** | ~40 | ❌ 0 stores | Failed (window.store_data) | 0% |
| **Glengarry** | 3-5 | ❌ 0 stores | Failed (DOM extraction) | 0% |
| **Black Bull** | 60+ | ❌ 0 stores | Failed (window data) | 0% |
| **TOTAL** | **~940** | **298** | Mixed | **31.7%** |

\* Liquorland has more stores than expected (167 vs target 100) - chain has expanded

### Product Price Coverage (Scrapers - December 26, 2025)

| Chain | Stores in NZ | Scraper Coverage | Pricing Model | Coverage % |
|-------|--------------|------------------|---------------|------------|
| **Countdown** | ~180 | All stores (180) | Chain-wide | 100% |
| **New World** | 144 | All stores (144) | Store-specific | 100% |
| **PakNSave** | 57 | All stores (57) | Store-specific | 100% |
| **Liquorland** | ~100 | All stores | Chain-wide | 100% |
| **Liquor Centre** | 90 | All stores (90) | Store-specific | 100% |
| **Super Liquor** | ~130 | All stores | Chain-wide | 100% |
| **Bottle O** | ~40 | All stores | Chain-wide | 100% |
| **Glengarry** | 3-5 | All stores | Chain-wide | 100% |
| **Thirsty Liquor** | 130+ | All stores (130+) | Chain-wide | 100% |
| **Black Bull** | 60+ | 3 stores only | Store-specific | **5%** |
| **TOTAL** | **~940** | **~883** | Mixed | **~94%** |

**Note**: Store location scrapers and product price scrapers are separate systems. Product price scrapers work via APIs/HTML parsing of product catalogs and have ~94% coverage. Store location scrapers extract physical store addresses/coordinates and currently have 31.7% coverage due to website structure changes.

### Store-Specific vs Chain-Wide Pricing

**Chain-Wide Pricing** (6 chains):
- Same product = same price at all locations
- Single scrape covers entire chain
- Faster, simpler implementation
- Chains: Countdown, Liquorland, Super Liquor, Bottle O, Glengarry, Thirsty Liquor

**Store-Specific Pricing** (4 chains):
- Prices vary by location/region
- Must scrape multiple stores for full coverage
- More complex, slower execution
- Chains: New World, PakNSave, Liquor Centre, Black Bull (limited coverage)

#### Pricing Model Determination Methodology

**Important Note**: The pricing model classifications (chain-wide vs store-specific) are **inferred from technical implementation patterns**, not empirically verified through price comparisons.

**How We Determine Pricing Models**:

1. **Store-Specific (Definitive)**:
   - **API requires store ID parameter**: New World, PakNSave
     - API calls explicitly filter by `storeId`
     - Cannot retrieve products without store selection
     - Evidence: `filters: f'stores:{self.store_id}'` in API requests
   - **Store-specific subdomains**: Liquor Centre
     - Each store has unique subdomain: `{store}.shop.liquor-centre.co.nz`
     - Separate catalogs per location
     - Evidence: 90 different store subdomains in use

2. **Chain-Wide (Inferred)**:
   - **No store parameter in API**: Countdown, Thirsty Liquor
     - Single catalog endpoint serves all stores
     - No store selection mechanism exposed
     - Assumption: If API doesn't require store, prices are uniform
   - **Single HTML catalog**: Liquorland, Super Liquor, Bottle O, Glengarry
     - Scraper fetches one catalog covering all stores
     - No store-specific URLs or parameters
     - Assumption: Single catalog implies uniform pricing

**Verification Needed**:
- Chain-wide classifications are **technical inferences**, not price-verified
- Possible edge cases:
  - Franchise stores may set their own prices despite "chain-wide" catalogs
  - Regional pricing differences might exist but not be exposed via API
  - API might aggregate prices from multiple stores
- **Recommendation**: Manually verify pricing across locations for critical use cases

**To Empirically Verify**:
1. Compare specific product prices across different physical store locations
2. Check retailer websites with different "selected store" locations
3. Contact chains directly to confirm pricing policies
4. Monitor scraped data for price variations by geographic region
5. **Cross-chain validation**: Compare prices for identical products across different chains
   - Sanity check: Scrapers should return realistic price variations (e.g., budget chains cheaper than premium)
   - Example: Compare "Steinlager Pure 12pk" across Countdown, PakNSave, New World, Liquorland
   - Significant price discrepancies may indicate scraper issues or promotional differences
   - Useful for detecting parsing errors (e.g., capturing cents instead of dollars)

### Expansion Capabilities

**Easy to Expand** (configured for single store, can do all):
- **New World**: Change `default_store_id` → instant access to any of 140 stores
- **PakNSave**: Change `default_store_id` → instant access to any of 60 stores
- **Liquor Centre**: Set `LIQUOR_CENTRE_ALL_STORES=true` → scrapes all 90+ stores

**To achieve 100% coverage across all stores**:
1. Enable multi-store mode for New World (140 stores)
2. Enable multi-store mode for PakNSave (60 stores)
3. Enable all stores for Liquor Centre (90 stores)
4. **Result**: Full coverage of ~750 stores nationwide

**Performance Implications**:
- Current: ~430 stores, ~10 minutes total
- Full coverage: ~750 stores, ~30-45 minutes total
- Recommended: Use distributed execution (Celery/RQ) for full coverage

---

## Chains Investigated But Excluded

The following liquor retailers were investigated but **not implemented** due to technical limitations or lack of value:

### Four Square

**Status**: ❌ Excluded - Not viable for scraping

**Chain Overview**:
- **Type**: Grocery/convenience store chain (not dedicated liquor retailer)
- **Stores**: 230+ locations nationwide
- **Parent Company**: Foodstuffs (same as New World, PakNSave)
- **Liquor Availability**: Many stores sell beer, wine, and spirits alongside groceries

**Why Excluded**:

1. **No Online Liquor Catalog**
   - Four Square sells liquor in physical stores only
   - Website has "Beer, Cider & Wine" category in specials, but displays **zero liquor products**
   - Likely due to age verification/regulatory restrictions on displaying alcohol online
   - Only promotional content (e.g., Sawmill Beach Day IPA partnership page)

2. **No Scrapable Data Source**
   - ❌ No public API for product data
   - ❌ No e-commerce platform (uses Uber Eats for delivery, not own system)
   - ❌ Server-side rendered Next.js with no exposed liquor product endpoints
   - Category filters exist but return no alcohol products

3. **Store-Specific Inventory**
   - Each store has different liquor selection (not centralized)
   - Examples from individual store pages:
     - Four Square Coromandel: "epic craft beer and cider range"
     - Four Square Māpua: "massive range of local wines and craft beers"
     - Four Square Fairlie: "premium beer, wine, and cheeses"
   - Would require scraping 230+ stores with no unified product database

4. **Redundant Coverage**
   - Already have comprehensive Foodstuffs coverage via:
     - New World: 144 stores (100% coverage)
     - PakNSave: 57 stores (100% coverage)
   - Four Square would provide duplicate/overlapping product data from same parent company
   - Four Square stores typically carry subset of New World/PakNSave liquor range

**Technical Investigation Results**:
- ✅ Tested API endpoints: All returned 404 or connection refused
- ✅ Checked specials page with filters: No liquor products visible
- ✅ Examined sitemap: Only promotional/recipe pages mentioning alcohol
- ✅ Analyzed page structure: Products embedded as JSON but only non-alcoholic items

**Recommendation**: Skip entirely - no technical path to scraping liquor products, and coverage already exists through sibling Foodstuffs brands.

**Investigated**: December 26, 2025

---

## Summary

Liquorfy successfully scrapes **10 major NZ liquor chains**:

- **5 API-based scrapers**: Fast, reliable (Countdown, New World, PakNSave, Thirsty Liquor, Black Bull)
- **5 HTML-based scrapers**: Necessary when no API exists (Liquorland, Liquor Centre, Super Liquor, Bottle O, Glengarry)

**Current Coverage**: ~883 stores (~94% of major liquor retailers in NZ)
**Total Stores in NZ**: ~940 stores across all chains

Each scraper is tailored to its target site:
- **Countdown**: Woolworths API - All 180 stores (chain-wide pricing)
- **New World**: Foodstuffs API - All 144 stores (store-specific pricing)
- **PakNSave**: Foodstuffs API - All 57 stores (store-specific pricing)
- **Liquorland**: Vue.js SSR hydration - All ~100 stores (chain-wide pricing)
- **Liquor Centre**: Multi-store subdomains - All 90 stores (store-specific pricing)
- **Super Liquor**: Traditional HTML - All ~130 stores (chain-wide pricing)
- **Bottle O**: GTM dataLayer extraction - All ~40 stores (chain-wide pricing)
- **Glengarry**: Legacy JSP parsing - All 3-5 stores (chain-wide pricing)
- **Thirsty Liquor**: Shopify API - All 130+ stores (chain-wide pricing)
- **Black Bull**: Shopify API - 3 stores only (~5% of 60+ stores, limited online presence)

**Chains Excluded**: Four Square (230+ stores) - no online liquor catalog, already covered by Foodstuffs brands

All scrapers are **production-ready** and actively maintained.

---

## Store Location Scraper Status (January 1, 2026)

### Current Coverage

- **Total Stores in Database**: 298
- **Overall Coverage**: 31.7% (298/940 stores)
- **Chains with Full Coverage**: 2 (Liquorland 167%, Super Liquor 101%)
- **Chains with Partial Coverage**: 1 (Thirsty Liquor 8%)
- **Chains with No Coverage**: 7

### Working Scrapers

✅ **Liquorland** (167 stores)
- Scraper: `LiquorlandLocationScraper`
- Method: Playwright browser automation + window object extraction
- Status: Fully functional
- Last scraped: January 1, 2026

✅ **Super Liquor** (131 stores)
- Scraper: `SuperLiquorLocationScraper`
- Method: Direct API call to `/getstorelocatordetails`
- Status: Fully functional
- Last scraped: Previously loaded (December 2025)

### Failed Scrapers

❌ **Countdown** (0 stores)
- Error: `Page.goto: net::ERR_HTTP2_PROTOCOL_ERROR`
- Likely cause: Bot detection / Cloudflare protection
- Recommendation: Investigate API endpoints or use manual data import

❌ **New World** (0 stores)
- Error: No stores found in DOM
- Scraper: Generic scraper
- Recommendation: Build dedicated scraper or investigate API

❌ **PakNSave** (0 stores)
- Error: No stores found in DOM
- Scraper: Generic scraper
- Recommendation: Build dedicated scraper or investigate API

❌ **Bottle O** (0 stores)
- Error: `window.store_data` not found
- Likely cause: Website structure changed
- Recommendation: Investigate current store data location

❌ **Black Bull** (0 stores)
- Error: `window.storeLocationsData` not found
- Likely cause: Website structure changed
- Recommendation: Investigate current store locator implementation

❌ **Glengarry** (0 stores)
- Error: No store elements found with any selector
- Likely cause: Website uses different DOM structure
- Recommendation: Manually inspect current website structure

⚠️ **Thirsty Liquor** (11 stores)
- Expected: 130+ stores
- Actual: 11 stores (8% coverage)
- Issue: Unknown - scraper runs but only finds 11 stores
- Recommendation: Debug window data extraction

### Next Steps to Improve Coverage

1. **High Priority** (Large Impact):
   - Countdown (180 stores): Bypass bot detection or find API
   - New World (144 stores): Build dedicated scraper with API investigation
   - Thirsty Liquor (130 stores): Fix partial scraper to get remaining 119 stores

2. **Medium Priority**:
   - PakNSave (57 stores): Same infrastructure as New World
   - Liquor Centre (90 stores): Investigate subdomain scraping

3. **Low Priority** (Small Impact):
   - Bottle O (40 stores): Update to new website structure
   - Black Bull (60 stores): Most stores don't have online presence
   - Glengarry (5 stores): Small chain, low impact

4. **Alternative Approach**:
   - Use existing store data files for New World/PakNSave (144 + 57 = 201 stores)
   - Requires geocoding addresses to get lat/lon coordinates
   - Could bring total coverage from 32% → 53%

---

**Last Updated**: January 1, 2026 (Store Location Database)
**Product Scrapers Last Updated**: December 26, 2025
**Maintainer**: Liquorfy Development Team
**Contact**: For issues, see GitHub Issues
