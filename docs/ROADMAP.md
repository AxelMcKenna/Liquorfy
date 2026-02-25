# Liquorfy — Go-to-Market Roadmap

**Created:** 2025-02-25
**Goal:** Launch Liquorfy as a legally defensible, production-ready liquor price comparison platform for New Zealand

---

## Current State Assessment

| Component | Status | Notes |
|-----------|--------|-------|
| **Backend API** | Functional | FastAPI + PostgreSQL/PostGIS + Redis. CI/CD pipeline exists. Deployment guide written. |
| **Scrapers** | 10 active | All functional but 4 have VERY HIGH legal risk, 3 have HIGH risk (see audit) |
| **Web frontend** | Functional | React 18 + Vite. Landing, Explore, filters, product cards, store map, location-aware |
| **iOS app** | Functional | SwiftUI. Explore, landing, product detail, store map, filters |
| **Infrastructure** | Ready | Docker Compose (prod), GHCR images, CI/CD pipeline. Deploy step is placeholder |
| **Legal compliance** | Not ready | No retailer permissions, active anti-detection measures, ToS violations identified |

**Bottom line:** The product is technically built. The blocker is legal/compliance risk, not engineering.

---

## Phase 0: Legal Foundation (Weeks 1-2)

_You cannot go to market on scraped data without addressing the compliance risks. This phase runs in parallel with everything else and is non-negotiable._

### 0.1 Engage NZ IP/Technology Lawyer
- [ ] Get a formal legal opinion on scraping publicly available price data in NZ
- [ ] Understand exposure under Copyright Act 1994, Fair Trading Act, Crimes Act s249
- [ ] Clarify enforceability of browse-wrap ToS in NZ courts
- [ ] Determine if price comparison qualifies as "fair dealing" under NZ copyright law
- [ ] **Output:** Written legal opinion with a risk matrix and go/no-go for each retailer

### 0.2 Retailer Outreach (Start Immediately)
- [ ] Draft a partnership pitch deck: Liquorfy drives foot traffic + online orders to retailers, in exchange for authorized data access
- [ ] Prioritize outreach by retailer risk level and market coverage:
  - **Tier 1 (highest priority):** Foodstuffs (New World + PakNSave — one conversation covers two chains), Woolworths NZ
  - **Tier 2:** Super Liquor, Liquorland (explicit anti-scraping ToS — need permission most urgently)
  - **Tier 3:** Liquor Centre, The Bottle-O (robots.txt blocks AI crawlers by name)
  - **Tier 4:** Glengarry, Thirsty Liquor, Black Bull (lower risk, smaller chains)
- [ ] Contact relevant business development or digital teams at each retailer
- [ ] **Output:** Documented permission status for each retailer (authorized / pending / denied)

### 0.3 Immediate Technical Compliance
- [ ] Remove `undetected_playwright` (Malenia stealth) from `browser_base.py` and `api_auth_base.py`
- [ ] Remove `--disable-blink-features=AutomationControlled` from browser launch args
- [ ] Standardize ALL scrapers to transparent User-Agent: `Liquorfy/1.0 (Price Comparison Bot; +https://liquorfy.co.nz)`
- [ ] Implement robots.txt parser — fetch and honor directives before each scrape
- [ ] Honor Glengarry's 10-second crawl-delay
- [ ] Add scraper kill-switch: ability to disable individual scrapers via config/env without code changes

### 0.4 Decide Initial Launch Retailer Set
Based on legal opinion + outreach responses, decide which retailers to include at launch:

**Best-case launch set (with permissions):** All 10 retailers
**Minimum viable launch set (without permissions):** Retailers where:
  - No explicit anti-scraping ToS exists
  - robots.txt permits crawling
  - Transparent User-Agent is used
  - Rate limits are respected

**Likely MVP set without any permissions:** Thirsty Liquor + Black Bull (Shopify public API, no explicit anti-scraping ToS) — but this is only 2 retailers and insufficient for a price comparison service.

**Realistic assessment:** You need at least 4-5 retailers including one major chain (Woolworths, PakNSave, or New World) to have a useful product. This means retailer partnerships are not optional — they are a launch dependency.

---

## Phase 1: Technical Hardening (Weeks 1-3)

_Runs in parallel with Phase 0. Get the product production-ready._

### 1.1 Scraper Architecture Refactor
- [ ] Implement per-retailer feature flags (enable/disable via env vars)
- [ ] Add robots.txt parser module (use `robotexclusionrulesparser` or similar)
- [ ] Build consent/permission tracking: record which retailers have granted permission, with expiry dates
- [ ] Replace auth token capture (Foodstuffs) with permission-based API access if obtained
- [ ] Add scraper health monitoring: alert on failures, track success rates

### 1.2 Data Freshness & Accuracy
- [ ] Implement stale data detection: flag/hide products not refreshed within 48 hours
- [ ] Add price change tracking: detect and log significant price movements
- [ ] Implement data validation: reject obviously wrong prices (negative, >$10,000, etc.)
- [ ] Add "last updated" timestamps visible to users per retailer
- [ ] Fair Trading Act compliance: ensure displayed prices are accurate and current

### 1.3 Image Handling
- [ ] Stop hotlinking retailer product images (bandwidth theft + copyright risk)
- [ ] Option A: Use generic product category icons instead of product photos
- [ ] Option B: Cache images on own CDN with retailer permission
- [ ] Option C: Link to retailer product pages instead of displaying images
- [ ] **Recommended for launch:** Option A (generic icons) until image permissions are secured

### 1.4 Production Infrastructure
- [ ] Finalize deployment target (recommended: DigitalOcean droplet or Fly.io for NZ latency)
- [ ] Configure production deploy step in CI/CD (currently placeholder)
- [ ] Set up SSL/TLS for liquorfy.co.nz
- [ ] Configure monitoring (UptimeRobot + Sentry for error tracking)
- [ ] Set up database backups (automated daily)
- [ ] Load test with realistic scraper + API traffic

---

## Phase 2: Launch Preparation (Weeks 3-5)

### 2.1 Legal & Compliance Pages
- [ ] Privacy Policy page (already exists at `/privacy` — review and finalize)
- [ ] Terms of Use for Liquorfy itself
- [ ] Add disclaimers: "Prices sourced from publicly available data. Verify in-store before purchasing."
- [ ] Add "Data sourced from [retailer name]" attribution per product
- [ ] Cookie consent if analytics are used

### 2.2 Product Polish
- [ ] Landing page copy and value proposition
- [ ] SEO fundamentals: meta tags, structured data (Product schema), sitemap
- [ ] Mobile responsive testing across devices
- [ ] Performance optimization: Core Web Vitals
- [ ] Error states: what happens when a retailer's data is unavailable?
- [ ] Empty states: messaging when no results match filters

### 2.3 Analytics & Measurement
- [ ] Set up privacy-respecting analytics (Plausible, Fathom, or self-hosted Umami)
- [ ] Track key events: searches, filter usage, retailer clicks, location grants
- [ ] Define success metrics for launch: DAU, searches/session, retailer click-through rate

### 2.4 iOS App Preparation
- [ ] Apple Developer account setup
- [ ] App Store listing: screenshots, description, keywords
- [ ] TestFlight beta distribution
- [ ] App Review guidelines compliance (age gate for alcohol content)
- [ ] Note: Apple requires age verification for alcohol-related apps

---

## Phase 3: Soft Launch (Weeks 5-7)

### 3.1 Deploy to Production
- [ ] Deploy API + worker + web to production server
- [ ] Run database migrations
- [ ] Seed store data
- [ ] Run initial scraper cycle for authorized retailers only
- [ ] Verify all health endpoints
- [ ] SSL + domain configured

### 3.2 Beta Testing
- [ ] Invite 20-50 beta users (friends, family, NZ tech community)
- [ ] Collect feedback on: accuracy, usability, missing retailers, bugs
- [ ] Monitor scraper stability under real conditions
- [ ] Monitor API performance and error rates
- [ ] Iterate on UX based on feedback

### 3.3 Content & Attribution
- [ ] Ensure every price shown attributes the source retailer
- [ ] Add "Visit [retailer] website" deep links for each product
- [ ] Frame Liquorfy as driving traffic TO retailers, not replacing them

---

## Phase 4: Public Launch (Weeks 7-9)

### 4.1 Web Launch
- [ ] Remove beta gates
- [ ] Submit to Google Search Console
- [ ] Social media presence (minimal: one landing page)
- [ ] Post to NZ subreddits, Geekzone, relevant communities
- [ ] Monitor for retailer complaints or cease-and-desist notices

### 4.2 iOS Launch
- [ ] Submit to App Store
- [ ] Handle App Review feedback
- [ ] Age verification gate (required for alcohol apps)

### 4.3 Monitor & Respond
- [ ] Daily monitoring of scraper health
- [ ] Weekly review of retailer permission status
- [ ] Respond promptly to any retailer takedown requests
- [ ] Track user growth and engagement

---

## Phase 5: Growth & Sustainability (Months 3-6)

### 5.1 Retailer Partnerships
- [ ] Convert informal permissions to formal data agreements
- [ ] Explore affiliate/referral revenue: earn commission when users click through to purchase
- [ ] Negotiate authorized API access where possible
- [ ] Offer retailers a dashboard showing traffic driven by Liquorfy

### 5.2 Product Expansion
- [ ] User accounts + price alerts ("notify me when X drops below $Y")
- [ ] Price history charts
- [ ] Shopping list / basket comparison
- [ ] "Cheapest basket" feature: find the best store for your full shopping list
- [ ] Community features: user ratings, reviews

### 5.3 Revenue Model
- [ ] **Affiliate links** — earn referral fees from retailer click-throughs (primary model)
- [ ] **Sponsored listings** — retailers pay to feature deals prominently
- [ ] **Premium features** — price alerts, advanced filtering, historical data
- [ ] **Data insights** — anonymized market data sold to industry (long-term)

### 5.4 Additional Retailers
- [ ] Investigate: Big Barrel, Henry's, Fine Wine Delivery Company, regional independents
- [ ] Build partnerships before scraping (lesson learned from Phase 0)

---

## Critical Path & Dependencies

```
Legal opinion (0.1) ─────────────────────┐
                                          ├─► Decide launch retailer set (0.4)
Retailer outreach (0.2) ─────────────────┘         │
                                                    │
Technical compliance (0.3) ──► Scraper refactor (1.1) ──► Deploy (3.1)
                                                    │
Production infra (1.4) ─────────────────────────────┘
                                                    │
Legal pages (2.1) ──► Product polish (2.2) ──► Beta (3.2) ──► Launch (4.1)
                                                              │
iOS prep (2.4) ───────────────────────────────────────► iOS Launch (4.2)
```

**The critical path is:** Legal opinion → Retailer permissions → Launch retailer set decision → Everything else follows.

Without retailer permissions, the technical product is ready but cannot be legally launched at scale.

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| All retailers deny permission | Pivot to partnership-first model; approach retailers with traffic/revenue data from beta |
| Cease-and-desist received | Immediately disable affected scraper; respond cooperatively; this is why kill-switches matter |
| Legal opinion says high risk | Consider alternative data sources: manual data entry, user-submitted prices, public API programs |
| App Store rejection (alcohol) | Ensure age gate is robust; follow Apple's alcohol app guidelines exactly |
| Scraper breakage post-launch | Monitor daily; maintain fixture/fallback data; show "data unavailable" rather than stale prices |
| Competitor launches first | Speed matters but legal foundation matters more; a legally sound product survives longer |

---

## Timeline Summary

| Week | Phase | Key Milestones |
|------|-------|---------------|
| 1-2 | Phase 0 + 1 | Lawyer engaged, outreach started, stealth removed, robots.txt parser built |
| 3 | Phase 1 | Feature flags, data freshness, image handling, infra finalized |
| 3-5 | Phase 2 | Legal pages, product polish, analytics, iOS prep |
| 5-7 | Phase 3 | Production deploy, beta testing, iteration |
| 7-9 | Phase 4 | Public web launch, iOS submission |
| 9+ | Phase 5 | Growth, partnerships, revenue |

**Estimated time to public launch: 7-9 weeks** (assuming at least one major retailer grants permission within 4 weeks).
