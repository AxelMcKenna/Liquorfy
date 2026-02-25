# Scraper Privacy & Terms of Service Audit

**Date:** 2025-02-25
**Scope:** All 10 active scrapers in the Liquorfy platform
**Purpose:** Evaluate each scraper against the target retailer's Terms of Service, Privacy Policy, robots.txt, and applicable New Zealand law

---

## Executive Summary

Liquorfy operates 10 scrapers targeting New Zealand liquor retailers. This audit evaluates each against the retailer's published Terms of Service (ToS), privacy policies, and robots.txt files, as well as the broader NZ legal landscape.

**Overall Risk Rating: MODERATE-HIGH**

| Risk Area | Assessment |
|-----------|-----------|
| Explicit ToS violations | **HIGH** — Super Liquor explicitly prohibits scraping by name; PakNSave/New World broadly prohibit copying/reproducing content |
| Anti-detection circumvention | **HIGH** — `undetected_playwright` stealth mode and `--disable-blink-features=AutomationControlled` actively evade bot detection |
| robots.txt compliance | **MODERATE** — Claimed in comments but no actual robots.txt parser exists; Woolworths NZ returns 503 (likely blocking non-browser access) |
| Copyright/IP risk | **MODERATE** — Product images are stored/referenced; price data IP claims are legally weaker but present |
| NZ Criminal law (s249/s252) | **LOW-MODERATE** — s252 likely doesn't apply to public websites; s249 (dishonest access for gain) is untested but theoretically applicable |
| Privacy law risk | **LOW** — No personal data is collected from retailers |

---

## Per-Retailer Assessment

### 1. Woolworths NZ (formerly Countdown)

| Aspect | Detail |
|--------|--------|
| **Scraper** | `countdown_api.py` — API-based (HTTP requests) |
| **Mechanism** | Direct HTTP calls to Woolworths internal API endpoints |
| **User-Agent** | Spoofed as Chrome browser: `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36` |
| **robots.txt** | Could not be fetched (returns 503) — suggests bot-blocking infrastructure |
| **ToS Status** | Full terms page uses JavaScript rendering, not indexed by search engines. The terms page exists at `woolworths.co.nz/info/terms-and-conditions/online-shopping-website-and-app` but could not be crawled |
| **Known Measures** | Woolworths employs CAPTCHAs, IP blocking, and bot detection |

**Risk Assessment: MODERATE-HIGH**
- The scraper masquerades as a real Chrome browser rather than identifying as Liquorfy
- Uses internal API endpoints not intended for third-party consumption
- Woolworths actively blocks automated access (503 on robots.txt)
- Rate limiting (0.5s between pages) is reasonable but the deceptive User-Agent is a concern

**Recommendations:**
- Switch to transparent User-Agent (`Liquorfy/1.0`) for API scraper
- Investigate whether Woolworths offers a partner/affiliate API
- The inability to read their ToS is itself a signal they don't want automated access

---

### 2. New World (Foodstuffs)

| Aspect | Detail |
|--------|--------|
| **Scraper** | `new_world_api.py` (extends `foodstuffs_base.py` + `api_auth_base.py`) |
| **Mechanism** | Browser-based auth to capture JWT tokens, then API calls |
| **User-Agent** | Spoofed Chrome UA for auth; spoofed Chrome UA for API calls |
| **ToS Key Clauses** | "The Online Services contain intellectual property and other proprietary information." IP rights owned/licensed by Foodstuffs. Users may not infringe IP rights (copying, modifying, reposting). Must not "disrupt or interfere with the Online Services or servers." |
| **robots.txt** | Could not be fetched |

**Risk Assessment: HIGH**
- Uses browser automation with stealth mode (`undetected_playwright`) to bypass Cloudflare/bot detection
- Captures JWT auth tokens via intercepted network requests — this goes beyond simple public page scraping
- ToS broadly prohibits copying content and disrupting/interfering with services
- Per-store scraping across 50+ stores amplifies load

**Recommendations:**
- The authentication bypass pattern (capturing JWTs via browser automation) is the highest-risk behavior in the codebase
- Explore formal data partnerships with Foodstuffs
- At minimum, respect rate limits and reduce per-store crawl frequency

---

### 3. PakNSave (Foodstuffs)

| Aspect | Detail |
|--------|--------|
| **Scraper** | `paknsave_api.py` (extends `foodstuffs_base.py` + `api_auth_base.py`) |
| **Mechanism** | Identical to New World (same API infrastructure, different domain) |
| **ToS Key Clauses** | Users may not "copy, modify, duplicate, create derivative works from, frame, mirror, republish, display, transmit, or distribute all or any portion" of the online shopping service. Must not "disrupt or interfere with the Online Services or servers." |
| **robots.txt** | Could not be fetched |

**Risk Assessment: HIGH**
- Same authentication bypass concerns as New World
- PakNSave's terms are **more explicit** about prohibiting copying/reproducing/distributing content
- The term "any portion" would encompass price data extraction
- Same stealth/anti-detection circumvention concerns

**Recommendations:**
- Same as New World — formal partnership is the safest path
- PakNSave's more explicit ToS language creates higher contractual risk

---

### 4. Super Liquor

| Aspect | Detail |
|--------|--------|
| **Scraper** | `super_liquor.py` — HTTP-based with pagination |
| **User-Agent** | **Transparent:** `Liquorfy/1.0 (Price Comparison Bot; +https://liquorfy.co.nz)` |
| **ToS Key Clauses** | **Section 1.3 — Intellectual Property:** Users are "expressly prohibited from reformatting, reproducing, reselling or copying, **by manual, or automated means such as scraping**, any information, data, or other material from the Website other than as strictly necessary to view the Website." **Section 1.2:** Content may only be accessed "for informational and non-commercial purposes." |
| **robots.txt** | Could not be fetched |

**Risk Assessment: VERY HIGH**
- **Super Liquor is the only retailer that explicitly prohibits scraping by name in their ToS**
- The term "automated means such as scraping" directly describes what this scraper does
- Content restricted to "non-commercial purposes" — a commercial price comparison service is squarely in violation
- However, the scraper uses a transparent User-Agent, which is a positive compliance signal

**Recommendations:**
- This is the highest legal risk in the portfolio — Super Liquor's ToS is unambiguous
- Seek written permission or a data partnership before continuing to scrape
- Consider removing this scraper until permission is obtained

---

### 5. Liquorland

| Aspect | Detail |
|--------|--------|
| **Scraper** | `liquorland.py` — Playwright headless browser |
| **User-Agent** | **Transparent:** `Liquorfy/1.0 (Price Comparison Bot; +https://liquorfy.co.nz)` |
| **Rate Limiting** | 1.0s between pages, 2.5s between categories — well-documented in code |
| **ToS** | Terms page exists at `liquorland.co.nz/terms-and-conditions` but full content could not be retrieved |
| **Additional Integration** | Also queries SaleFinder API (`salefinder.co.nz`) for promotional data |
| **Code Claim** | Docstring states "robots.txt compliance" |

**Risk Assessment: MODERATE**
- Transparent User-Agent is a positive signal
- Respectful rate limiting is documented and implemented
- The code claims robots.txt compliance but there is **no actual robots.txt parser** in the codebase — compliance is asserted, not verified
- Uses browser automation with resource blocking (images, fonts, stylesheets)
- SaleFinder API integration appears to use a public API endpoint

**Recommendations:**
- Implement actual robots.txt parsing rather than claiming compliance
- Attempt to fetch and honor the actual robots.txt directives
- The transparent UA + reasonable rate limits make this one of the better-behaved scrapers

---

### 6. Thirsty Liquor (Shopify)

| Aspect | Detail |
|--------|--------|
| **Scraper** | `thirsty_liquor.py` — Shopify `products.json` API |
| **Mechanism** | HTTP requests to `/collections/{name}/products.json` endpoints |
| **User-Agent** | Default httpx User-Agent (not customized) |
| **Shopify ToS** | Shopify's Terms of Service state: "You agree not to access the Services or monitor any material or information from the Services using any robot, spider, scraper, or other automated means" |
| **Store-specific ToS** | No website usage ToS found for Thirsty Liquor specifically (only competition and loyalty T&Cs) |
| **robots.txt** | Shopify stores typically have a robots.txt; could not fetch this one |

**Risk Assessment: MODERATE**
- `products.json` is a publicly accessible Shopify endpoint — widely scraped across the industry
- Shopify's platform-level ToS prohibits automated access, but enforcement is typically through rate limiting rather than legal action against third parties
- The store owner (Thirsty Liquor) has no explicit website usage terms
- Rate limiting is present (0.5s between pages, 0.5s between collections)

**Recommendations:**
- This is lower risk than browser-based scrapers given the public API nature
- Consider reaching out to Thirsty Liquor for permission
- Add transparent User-Agent header

---

### 7. Black Bull (Shopify)

| Aspect | Detail |
|--------|--------|
| **Scraper** | `black_bull.py` — Per-store Shopify API |
| **Mechanism** | HTTP requests to individual store Shopify domains (`products.json`) |
| **User-Agent** | Default httpx User-Agent |
| **ToS** | No general website usage terms found — only competition and loyalty T&Cs |
| **robots.txt** | Could not be fetched |

**Risk Assessment: LOW-MODERATE**
- Same Shopify `products.json` considerations as Thirsty Liquor
- Only ~10 stores have online ordering via Shopify (small footprint)
- Rate limiting present (0.5s between pages, 0.5s between stores)
- No explicit anti-scraping terms found

**Recommendations:**
- Lower risk given small scale and public API endpoints
- Add transparent User-Agent header

---

### 8. Liquor Centre (CityHive/Myfoodlink Platform)

| Aspect | Detail |
|--------|--------|
| **Scraper** | `liquor_centre.py` — Playwright headless browser |
| **Mechanism** | Per-store browser scraping across ~90 store subdomains |
| **User-Agent** | Spoofed Chrome: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36` |
| **ToS** | Standard e-commerce terms (age verification, pricing disclaimers, accuracy disclaimers). No explicit anti-scraping clauses found |
| **robots.txt** | Could not be fetched |

**Risk Assessment: MODERATE**
- Per-store scraping across 90 stores creates significant aggregate load
- Spoofed User-Agent rather than transparent identification
- No explicit anti-scraping ToS found, but standard IP/copyright clauses likely apply
- Uses `undetected_playwright` stealth if available

**Recommendations:**
- Switch to transparent User-Agent
- Consider reducing scrape frequency given 90-store footprint
- The aggregate load across 90 subdomains is a concern even with per-request delays

---

### 9. The Bottle-O (CityHive Platform)

| Aspect | Detail |
|--------|--------|
| **Scraper** | `bottle_o.py` — Hybrid: per-store Playwright browser + franchise GTM dataLayer extraction |
| **Mechanism** | Per-store CityHive scraping + fallback franchise catalog extraction via Google Tag Manager `dataLayer` |
| **User-Agent** | Spoofed Chrome: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36` |
| **ToS** | Standard CityHive e-commerce terms — standard pricing, accuracy, and consumer law clauses. No explicit anti-scraping terms found |
| **robots.txt** | Could not be fetched |
| **Rate Limiting** | 2.5s between categories, 1.5s between requests |

**Risk Assessment: MODERATE**
- GTM `dataLayer` extraction is a grey area — this data is pushed to the browser for analytics but extracting it for commercial use is questionable
- Per-store scraping footprint is smaller than Liquor Centre
- Spoofed User-Agent is a concern
- No explicit anti-scraping ToS

**Recommendations:**
- Switch to transparent User-Agent
- GTM dataLayer extraction should be evaluated for appropriateness — this data is intended for analytics, not third-party consumption

---

### 10. Glengarry Wines

| Aspect | Detail |
|--------|--------|
| **Scraper** | `glengarry.py` — Extends `BrowserScraper` base class |
| **Mechanism** | Playwright headless browser |
| **User-Agent** | Spoofed Chrome (from `BrowserScraper` base): `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...` |
| **ToS** | Terms page at `glengarrywines.co.nz/termsconditions` — no anti-scraping clauses found in indexed content; full terms may be behind a dynamic link |
| **robots.txt** | Could not be fetched |

**Risk Assessment: MODERATE**
- Standard browser-based scraping with stealth capabilities
- No explicit anti-scraping ToS found (but full terms couldn't be verified)
- Single chain (no per-store amplification)
- Uses `BrowserScraper` base class with anti-detection features

**Recommendations:**
- Switch to transparent User-Agent
- Verify full terms page content manually

---

## Cross-Cutting Concerns

### 1. Anti-Detection / Stealth Measures (HIGH CONCERN)

The codebase includes several active anti-detection measures that undermine compliance claims:

| Measure | Location | Concern Level |
|---------|----------|---------------|
| `undetected_playwright` (Malenia stealth) | `browser_base.py:29`, `api_auth_base.py:16` | **HIGH** — Actively evades bot detection |
| `--disable-blink-features=AutomationControlled` | `browser_base.py:79` | **HIGH** — Hides automated browser fingerprint |
| Spoofed Chrome User-Agent | `browser_base.py:92`, `foodstuffs_base.py:137`, `countdown_api.py:60` | **MODERATE** — Misrepresents identity |
| Realistic viewport, locale, timezone | `browser_base.py:93-96` | **LOW** — Standard browser emulation |
| Resource blocking (images, fonts) | `browser_base.py:98-114` | **LOW** — Reduces load, acceptable |

**Analysis:** If a retailer has implemented bot detection, actively circumventing it undermines any good-faith argument. The combination of stealth mode + spoofed User-Agent + anti-detection browser args creates the appearance of intentionally deceptive access. This conflicts with the transparent `Liquorfy/1.0` User-Agent used by the HTTP-based scrapers (Super Liquor, Liquorland).

### 2. robots.txt Compliance (MODERATE CONCERN)

- The `liquorland.py` docstring claims "robots.txt compliance" (line 3)
- **No robots.txt parser exists anywhere in the codebase**
- Rate limiting delays are hardcoded, not derived from `Crawl-delay` directives
- Most retailer robots.txt files could not be fetched (503 or unreachable), suggesting many actively block automated access at the infrastructure level

### 3. Inconsistent User-Agent Strategy (MODERATE CONCERN)

The codebase uses two contradictory approaches:

| Approach | Scrapers | Signal |
|----------|----------|--------|
| **Transparent** (`Liquorfy/1.0 Price Comparison Bot`) | Super Liquor, Liquorland, store location scrapers | Good faith, identifiable |
| **Spoofed** (Chrome/Safari UA) | Countdown, Foodstuffs, Liquor Centre, Bottle-O, Glengarry, browser base class | Deceptive, conceals automated nature |

This inconsistency suggests the spoofed UAs are used precisely because transparent identification would result in being blocked.

### 4. Authentication Token Capture (HIGH CONCERN)

The `api_auth_base.py` class captures JWT tokens and session cookies by:
1. Opening a headless browser with stealth mode
2. Navigating to the retailer's website
3. Intercepting network requests to capture auth tokens
4. Using captured tokens for subsequent API calls

This pattern of capturing authentication credentials through automated browser sessions to access authenticated APIs is the highest-risk behavior in the codebase. It goes beyond scraping publicly visible pages.

### 5. Image URL Storage (LOW-MODERATE CONCERN)

All scrapers capture and store product image URLs. While the images aren't downloaded/hosted by Liquorfy (they're hotlinked from retailer CDNs), displaying retailer product images on the Liquorfy platform could constitute:
- Copyright infringement (images are creative works)
- Bandwidth theft (hotlinking)
- Trademark concerns (retailer logos in product images)

---

## New Zealand Legal Landscape

### Relevant Legislation

| Law | Relevance | Risk |
|-----|-----------|------|
| **Crimes Act s252** (Unauthorized computer access) | Accessing a public website likely doesn't constitute "unauthorized access" — s252 explicitly excludes using a system for non-permitted purposes | **LOW** |
| **Crimes Act s249** (Dishonest access for pecuniary advantage) | Broader provision — accessing computer systems to obtain commercial advantage. Untested in scraping context but theoretically applicable | **LOW-MODERATE** |
| **Copyright Act 1994** | Product descriptions, images are protected. Price data alone has weaker protection but may be part of a "database" | **MODERATE** |
| **Fair Trading Act 1986** | Price comparison must display accurate, current prices. Stale data could be misleading | **LOW** (if data is kept current) |
| **Contract law** (ToS as browse-wrap agreement) | ToS prohibitions may be enforceable if notice is sufficient. "Browse-wrap" agreements have weaker enforceability than "click-wrap" | **MODERATE** |

### Key NZ Precedents & Guidance

- **Trade Me v. third-party developers:** Trade Me successfully pursued developers who created scraping tools for their platform
- **Geekzone legal discussion:** NZ legal commentators note that "courts appear willing to mould existing laws to find a legal wrong committed by the scraper"
- **CIO NZ guidance:** "Extracting information from well-resourced companies, extracting sensitive or proprietary information, or using the information in a way which adversely impacts on the company's bottom line will put you squarely in the firing line"

---

## Risk Summary by Retailer

| Retailer | Risk Level | Key Issue |
|----------|-----------|-----------|
| **Super Liquor** | **VERY HIGH** | ToS explicitly prohibits "automated means such as scraping" |
| **New World** | **HIGH** | Auth token capture + stealth mode + broad IP/copying prohibitions |
| **PakNSave** | **HIGH** | Auth token capture + stealth mode + explicit "any portion" copying prohibition |
| **Woolworths NZ** | **MODERATE-HIGH** | Active bot blocking infrastructure + spoofed UA + internal API access |
| **Liquorland** | **MODERATE** | Transparent UA, but stealth browser + unverified robots.txt claim |
| **Liquor Centre** | **MODERATE** | 90-store footprint + spoofed UA + stealth browser |
| **The Bottle-O** | **MODERATE** | GTM dataLayer extraction + spoofed UA |
| **Glengarry** | **MODERATE** | Standard browser scraping + spoofed UA |
| **Thirsty Liquor** | **MODERATE** | Shopify platform ToS prohibits automated access |
| **Black Bull** | **LOW-MODERATE** | Small scale Shopify scraping, no explicit anti-scraping terms |

---

## Recommendations

### Immediate Actions (High Priority)

1. **Cease scraping Super Liquor** until written permission is obtained — their ToS unambiguously prohibits this activity by name
2. **Remove anti-detection/stealth measures** (`undetected_playwright`, `--disable-blink-features=AutomationControlled`) — these undermine any good-faith compliance argument
3. **Standardize on transparent User-Agent** (`Liquorfy/1.0 (Price Comparison Bot; +https://liquorfy.co.nz)`) across ALL scrapers
4. **Review the auth token capture pattern** for Foodstuffs scrapers — this is the highest technical risk in the codebase

### Medium-Term Actions

5. **Implement actual robots.txt parsing** — fetch and honor robots.txt before scraping each site
6. **Seek formal data partnerships** — approach retailers (especially Foodstuffs, Woolworths, Super Liquor) about authorized API access or data feeds
7. **Add ToS monitoring** — periodically check retailer ToS for changes that affect scraping legality
8. **Reduce aggregate load** — for per-store scrapers (Liquor Centre, Bottle-O, New World, PakNSave), consider longer intervals between stores

### Long-Term Actions

9. **Obtain legal counsel** — engage a NZ lawyer specializing in technology/IP law to review the full operation
10. **Build retailer relationships** — price comparison can benefit retailers (drives traffic); frame partnerships as mutually beneficial
11. **Consider public API alternatives** — some retailers may have affiliate programs or public product feeds
12. **Document compliance posture** — maintain a living document of which retailers have been contacted and their responses

---

## Methodology

This audit was conducted by:
1. Reading all scraper source code in `api/app/scrapers/`
2. Analyzing the technical mechanisms (User-Agent strings, anti-detection measures, rate limiting)
3. Researching each retailer's published Terms of Service and Privacy Policies via web search
4. Attempting to fetch each retailer's robots.txt file
5. Researching applicable New Zealand legislation and case law
6. Cross-referencing scraper behavior against identified ToS provisions

**Limitations:**
- Several retailer ToS pages use JavaScript rendering and could not be fully retrieved
- Most retailer robots.txt files returned 503 errors or were unreachable
- This is a technical/policy audit, not legal advice — consult qualified legal counsel for definitive guidance
