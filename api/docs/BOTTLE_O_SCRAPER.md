# The Bottle O Scraper

## Overview
Scraper for The Bottle O NZ using GTM dataLayer extraction with full database integration.

## Implementation
- **File**: `api/app/scrapers/bottle_o.py`
- **Chain**: `bottle_o`
- **Method**: Browser-based (Playwright) extracting from `window.gtmDataLayer`

## Features
✅ Full database integration via base `Scraper` class
✅ Extracts products from Google Tag Manager dataLayer
✅ Respects robots.txt policies
✅ Rate limiting (2.5s between categories)
✅ Respectful user agent identification
✅ Auto-creates prices for all Bottle O stores

## Robots.txt Compliance

### What we checked:
```bash
curl https://thebottleo.co.nz/robots.txt
```

### Findings:
- ✅ `/search` URLs are **NOT blocked** for general user agents
- ✅ Only specific bots (ClaudeBot, AhrefsBot, etc.) are disallowed
- ✅ Only specific paths blocked: `/lmg/`, `/order_lines/`, `/feedback`

### Our compliance:
1. **User Agent**: `Liquorfy/1.0 (Price Comparison Bot; +https://liquorfy.co.nz)`
2. **Rate Limiting**: 2.5 seconds between category requests
3. **Paths Accessed**: Only `/search?q[]=category:...` (allowed)
4. **Respectful**: Browser closes properly, no aggressive crawling

## Performance

### Test Results (2025-12-21):
- **Total products scraped**: 204
- **Categories**: 5 (beer, wine, spirits, rtd, cider)
- **Database**: All 204 products saved successfully
- **Failures**: 0
- **Duration**: ~48 seconds

### Data Quality:
- **Brand**: 100% (204/204 from GTM data)
- **Volume**: 37% (76/204 parsed from product names)
- **ABV**: 17% (35/204 extracted from product names)

## Categories Scraped

1. **Beer** - 48 products
2. **Wine** - 48 products
3. **Spirits** - 48 products
4. **RTD** - 48 products
5. **Cider** - 12 products

## Usage

### Basic scrape:
```python
from app.scrapers.bottle_o import BottleOScraper

scraper = BottleOScraper(use_fixtures=False)
run = await scraper.run()
print(f"Scraped {run.items_total} products")
```

### Test without DB:
```bash
python test_bottle_o.py
```

### Test with DB integration:
```bash
python test_bottle_o_db.py
```

## Technical Details

### Data Extraction:
- Navigates to search URLs for each category
- Waits for `window.gtmDataLayer` to populate (5s)
- Extracts JSON-encoded product impressions
- Parses: ID, name, price, brand, category

### Enrichment:
- Volume parsing from product names
- ABV extraction from product names
- Brand inference (if not in GTM data)
- Category inference (if not in GTM data)

### Database:
- Creates/updates `Product` records
- Creates `Price` records for all Bottle O stores
- Tracks price changes over time
- Records in `IngestionRun` for monitoring

## Limitations

1. **Store Availability**: Currently assigns products to all stores (no per-store availability)
2. **Image URLs**: Not available in GTM dataLayer (NULL in database)
3. **Promotions**: Not extracted yet (TODO)
4. **Product Details**: Only data from listing pages (no detail page scraping)

## Future Improvements

- [ ] Extract store-specific availability
- [ ] Get product images
- [ ] Parse promotional offers
- [ ] Handle pagination if categories exceed 48 products
- [ ] Extract additional product attributes from detail pages

## Notes

- The site uses Hotwired Turbo Rails for dynamic content
- Products load via JavaScript into GTM dataLayer
- Individual product detail pages return 404 on main domain
- Store selection required on shop subdomain for purchases
