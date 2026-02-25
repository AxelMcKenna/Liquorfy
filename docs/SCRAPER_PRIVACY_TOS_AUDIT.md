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
| Explicit ToS violations | **VERY HIGH** — Super Liquor, Liquorland, and Liquor Centre explicitly prohibit scraping by name; PakNSave/New World broadly prohibit copying/reproducing content |
| Anti-detection circumvention | **HIGH** — `undetected_playwright` stealth mode and `--disable-blink-features=AutomationControlled` actively evade bot detection |
| robots.txt violations | **VERY HIGH** — The Bottle-O and Liquor Centre explicitly block `ClaudeBot`, `anthropic-ai` by name in robots.txt; Glengarry has 10s crawl-delay; no robots.txt parser exists in codebase |
| Copyright/IP risk | **MODERATE** — Product images are stored/referenced; price data IP claims are legally weaker but present; every retailer claims IP over all content |
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
| **ToS Key Clauses** | **EXPLICIT anti-scraping:** Prohibits use of "any robot, spider, site search and retrieval application or other mechanism to retrieve or index any portion of the Site." Also prohibits: "reproduce, reformat, scrape, copy or resell any portion of the website and its contents." Downloaded materials may not be used for "commercial use." |
| **robots.txt** | `User-agent: *`, `Allow: /`. Blocks admin, checkout, account, search params, comparison features. No crawl-delay. Generally permissive for content pages. |
| **Additional Integration** | Also queries SaleFinder API (`salefinder.co.nz`) for promotional data |
| **Code Claim** | Docstring states "robots.txt compliance" |

**Risk Assessment: VERY HIGH**
- **Liquorland explicitly prohibits robots, spiders, scraping, reformatting, and reselling in their ToS**
- Commercial use is explicitly prohibited
- The code claims robots.txt compliance but there is **no actual robots.txt parser** in the codebase
- Transparent User-Agent is a positive signal but does not overcome the explicit ToS prohibition
- SaleFinder API integration appears to use a public API endpoint

**Recommendations:**
- Seek written permission from Liquorland before continuing to scrape
- Implement actual robots.txt parsing rather than claiming compliance
- The transparent UA + reasonable rate limits are good faith signals but insufficient given explicit ToS prohibition

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

### 8. Liquor Centre (Myfoodlink Platform)

| Aspect | Detail |
|--------|--------|
| **Scraper** | `liquor_centre.py` — Playwright headless browser |
| **Mechanism** | Per-store browser scraping across ~90 store subdomains |
| **User-Agent** | Spoofed Chrome: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36` |
| **ToS Key Clauses** | **EXPLICIT anti-scraping:** Prohibits "use any robot, spider, site search and retrieval application or other mechanism to retrieve or index any portion of the Site." Also prohibits: "modify, adapt, translate or reverse engineer any portion of the Site." Cannot "take any action that imposes...an unreasonable or disproportionately large load on our infrastructure." Copyright owned by or licensed to them. |
| **robots.txt** | **HIGHLY RESTRICTIVE** — Explicitly blocks AI crawlers by name: `anthropic-ai`, `ClaudeBot`, `Amazonbot`, `SemrushBot`, `AhrefsBot` and many others with `Disallow: /` |

**Risk Assessment: VERY HIGH**
- **Liquor Centre explicitly names "robot, spider" in anti-scraping ToS**
- **robots.txt explicitly blocks `ClaudeBot` and `anthropic-ai` by name** — a strong signal of hostility to AI/automated data collection
- Per-store scraping across 90 stores creates significant aggregate load
- Spoofed User-Agent rather than transparent identification
- Uses `undetected_playwright` stealth if available

**Recommendations:**
- This is one of the highest-risk scrapers — explicit ToS + explicit robots.txt bot blocking
- Seek written permission before continuing
- At minimum, honor the robots.txt (which currently blocks all automated access)

---

### 9. The Bottle-O (Myfoodlink Platform)

| Aspect | Detail |
|--------|--------|
| **Scraper** | `bottle_o.py` — Hybrid: per-store Playwright browser + franchise GTM dataLayer extraction |
| **Mechanism** | Per-store scraping + fallback franchise catalog extraction via Google Tag Manager `dataLayer` |
| **User-Agent** | Spoofed Chrome: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36` |
| **ToS Key Clauses** | "You agree not to use any device, software or routine to interfere or attempt to interfere with the proper working of this website." Reproduction, modification, distribution, republication of content is "strictly prohibited." Material only permitted for "personal non-commercial use or for good faith commercial dealings with Bottle-O." |
| **robots.txt** | **MOST RESTRICTIVE OF ALL RETAILERS** — Explicitly blocks by name: `anthropic-ai`, `ClaudeBot`, `Claude-SearchBot`, `Amazonbot`, `meta-externalagent`, `meta-webindexer`, plus many SEO bots (`SemrushBot`, `AhrefsBot`, `MJ12bot`, `DotBot`, etc.) and niche bots (`wine-searcherbot`, `GeedoProductSearch`) |
| **Rate Limiting** | 2.5s between categories, 1.5s between requests |

**Risk Assessment: VERY HIGH**
- **The Bottle-O has the most aggressive robots.txt of all retailers**, explicitly naming and blocking ClaudeBot, anthropic-ai, and Claude-SearchBot
- ToS prohibits interference with website and all reproduction/distribution beyond personal use
- GTM `dataLayer` extraction is a grey area — data intended for analytics, not third-party consumption
- Spoofed User-Agent actively conceals automated nature

**Recommendations:**
- The robots.txt is unambiguous — The Bottle-O does not want automated AI/bot access
- Seek explicit written permission before continuing
- GTM dataLayer extraction should be discontinued

---

### 10. Glengarry Wines

| Aspect | Detail |
|--------|--------|
| **Scraper** | `glengarry.py` — Extends `BrowserScraper` base class |
| **Mechanism** | Playwright headless browser |
| **User-Agent** | Spoofed Chrome (from `BrowserScraper` base): `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...` |
| **ToS Key Clauses** | "You may not display or distribute the content of any part of the website or its content in public, including any reproduction in any form on the Internet, without our express permission." Personal use only. No explicit bot/scraping prohibition but broad reproduction ban. |
| **robots.txt** | `User-agent: *` with **Crawl-delay: 10** (10 seconds between requests). Blocks login, registration, and service paths. Otherwise relatively open. |

**Risk Assessment: MODERATE**
- No explicit anti-scraping ToS language, but reproduction/distribution on the Internet is prohibited without permission
- **robots.txt specifies 10-second crawl-delay** — the scraper's 1.0s delay between pages violates this directive
- Single chain (no per-store amplification)
- Uses `BrowserScraper` base class with anti-detection features

**Recommendations:**
- Increase delay to honor the 10-second crawl-delay in robots.txt
- Switch to transparent User-Agent
- Seek permission for Internet reproduction of content

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

### 2. robots.txt Compliance (VERY HIGH CONCERN)

- The `liquorland.py` docstring claims "robots.txt compliance" (line 3)
- **No robots.txt parser exists anywhere in the codebase**
- Rate limiting delays are hardcoded, not derived from `Crawl-delay` directives
- **The Bottle-O and Liquor Centre explicitly block `ClaudeBot`, `anthropic-ai`, and `Claude-SearchBot` by name** in their robots.txt
- **Glengarry specifies a 10-second crawl-delay** that the scraper violates (uses 1.0s)
- **Thirsty Liquor blocks `Nutch` entirely** and has crawl-delays for specific bots
- **Black Bull blocks `Amazonbot`** and has crawl-delays for `msnbot` and `Slurp`
- Woolworths NZ returns 503 on robots.txt (infrastructure-level blocking)

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
| **Super Liquor** | **VERY HIGH** | ToS explicitly prohibits "automated means such as scraping" including "pricing information" |
| **Liquorland** | **VERY HIGH** | ToS explicitly prohibits "robot, spider...scrape, copy or resell"; commercial use banned |
| **Liquor Centre** | **VERY HIGH** | ToS names "robot, spider"; robots.txt blocks `ClaudeBot`/`anthropic-ai` by name |
| **The Bottle-O** | **VERY HIGH** | Most aggressive robots.txt — blocks `ClaudeBot`, `anthropic-ai`, `Claude-SearchBot` by name |
| **Woolworths NZ** | **HIGH** | Infrastructure blocks all non-browser access (503); likely mirrors AU anti-scraping terms |
| **New World** | **HIGH** | Auth token capture + stealth mode + broad IP/copying prohibitions |
| **PakNSave** | **HIGH** | Auth token capture + stealth mode + explicit "any portion" copying prohibition |
| **Black Bull** | **MODERATE-HIGH** | Broad "unauthorized means" clause; robots.txt blocks Amazonbot |
| **Glengarry** | **MODERATE** | 10s crawl-delay violated; reproduction/Internet distribution prohibited |
| **Thirsty Liquor** | **MODERATE** | Shopify platform ToS prohibits automated access; Nutch blocked in robots.txt |

---

## Recommendations

### Immediate Actions (High Priority)

1. **Cease scraping Super Liquor, Liquorland, Liquor Centre, and The Bottle-O** until written permission is obtained — all four have explicit anti-scraping ToS and/or robots.txt that specifically blocks AI/bot crawlers by name
2. **Remove anti-detection/stealth measures** (`undetected_playwright`, `--disable-blink-features=AutomationControlled`) — these undermine any good-faith compliance argument
3. **Standardize on transparent User-Agent** (`Liquorfy/1.0 (Price Comparison Bot; +https://liquorfy.co.nz)`) across ALL scrapers
4. **Review the auth token capture pattern** for Foodstuffs scrapers — this is the highest technical risk in the codebase
5. **Honor Glengarry's 10-second crawl-delay** — current 1.0s delay directly violates their robots.txt

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
