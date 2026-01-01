# Liquorland Store Selection Investigation

## Summary

Liquorland uses a complex store selection system where:
- **166 stores** across New Zealand with different pricing
- Some products show **default pricing** (no store selection needed)
- Some products **require store selection** to show pricing (marked with `no-cta` class)

## Key Findings

### 1. Store Data Structure

**API Endpoint**: `https://www.liquorland.co.nz/store-locations`

Stores are available as a JavaScript object with the following structure:

```json
{
  "storeid": 4,
  "label": "Liquorland Parnell",
  "code": "242",
  "url": "liquorland-parnell",
  "address": "347 Parnell Road\nParnell\n1052\nAuckland",
  "phone": "09 377 1672",
  "latitude": "-36.857800",
  "longitude": "174.781959",
  ...
}
```

- **Total stores**: 166
- **Store IDs**: 4, 6, 7, 8, 9, 10, 14, 15, 16, 17, ...
- **Store codes**: "242", etc.

### 2. Product Pricing Behavior

When scraping without a store selected:
- **Product 1** (Monteiths): Shows $28.99 (default price)
- **Product 2** (Rekorderlig): No price shown, has `no-cta` class (requires store)
- **Product 3** (Somersby): Shows $24.99 (default price)

### 3. Store Selection Workflow

The UI workflow for selecting a store:
1. Click the "Choose a store for pricing and availability" button
2. Modal appears with "Select a store" button
3. Click "Select a store" → Shows "Find Your Store" modal
4. Click "See All Liquorland Stores" → Loads store list (166 stores)
5. Click on a specific store → Sets store preference

### 4. Technical Implementation

**Age Gate**: Must be handled first (blocks all interactions)
- Selector: `#popup[role="dialog"]`
- Saves to localStorage as `ageConfirmed`

**Store Selector Button**:
- Found via: `[class*="store-select"], button[class*="store"]`
- Text: "for pricing and availability. Choose a store"

**Store List**:
- 166 stores loaded from `/store-locations` and `/store-locations-js/`
- Each store is a `li[class*="store"]` element
- Stores include full details (name, address, hours, etc.)

### 5. Data Storage Files

- `/tmp/liquorland_stores.json` - Complete store list with all 166 stores
- `/tmp/liquorland_store_modal.png` - Screenshot of initial store selector modal
- `/tmp/liquorland_store_list.png` - Screenshot of "Find Your Store" modal

## Challenges for Per-Store Scraping

### Scale Challenge
- **166 stores** × **14 product categories** = **2,324 page loads**
- With 1-second delay between requests: ~40 minutes minimum
- With realistic page loads and rate limiting: 1-2 hours per full scrape

### Technical Complexity
- Multi-step UI interaction required (modals, clicks)
- Need to maintain store context across page navigations
- Unknown if store selection persists via cookie, localStorage, or session

### Current Limitation
- Current scraper only captures products with default pricing
- Products requiring store selection are skipped (marked with `no-cta` class)
- This means we're missing some products entirely

## Options for Implementation

### Option 1: Full Per-Store Scraping (Comprehensive but Slow)
**Approach**: Iterate through all 166 stores, scraping each category for each store

**Pros**:
- Complete store-specific pricing data
- Captures all products including those with `no-cta`

**Cons**:
- Very slow (1-2 hours per full scrape)
- High server load (respectful rate limiting required)
- Complex implementation (store selection UI automation)
- Maintenance overhead (UI changes could break automation)

### Option 2: API-Based Approach (if available)
**Approach**: Find and use API endpoints that return store-specific pricing

**Pros**:
- Much faster than UI automation
- More reliable (less prone to UI changes)
- Lower resource usage

**Cons**:
- Need to discover/reverse-engineer API
- May require authentication or special headers
- API may not exist or may be rate-limited

### Option 3: Hybrid Approach (Recommended)
**Approach**:
1. Scrape products with default pricing (current behavior)
2. For products with `no-cta`, make targeted per-store requests
3. Prioritize high-traffic stores or specific regions

**Pros**:
- Balances coverage with performance
- Can be implemented incrementally
- Reduces total scrape time significantly

**Cons**:
- More complex logic
- May not have complete per-store data for all products

### Option 4: Deferred Implementation
**Approach**: Accept current limitation, move to other scrapers (Bottle-O), revisit later

**Pros**:
- Faster progress on overall project
- Can gather user requirements first
- Allows testing with partial data

**Cons**:
- Incomplete data for Liquorland
- Missing some products entirely

## Recommendation

**Start with Option 4** (defer per-store scraping):
1. Current Liquorland scraper captures products with default pricing
2. Move forward with Bottle-O scraper (as user requested)
3. Gather data on which products actually need per-store pricing
4. Return to implement Option 3 (hybrid) with informed priorities

This allows us to:
- Make progress on other scrapers
- Understand the actual data needs
- Implement per-store scraping more efficiently later

## Next Steps

- [x] Investigate store selection mechanism
- [ ] Decide on implementation approach (recommend Option 4)
- [ ] Build Bottle-O scraper
- [ ] Test Bottle-O scraper
- [ ] Return to Liquorland per-store scraping with better context
