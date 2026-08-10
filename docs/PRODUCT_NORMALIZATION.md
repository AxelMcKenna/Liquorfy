# Product Normalization Deep Dive — Interview Prep

**A code-grounded walkthrough of how Liquorfy turns ten retailers' inconsistent product text into one comparable catalogue.**

**Scope:** this document is a focused expansion of the "Entity resolution" thread in `LIQUORFY_INTERVIEW_HANDBOOK.md`. That handbook gives the 2-sentence answer; this gives the whiteboard-able one — the actual regexes, the actual hash key, the actual bugs that got fixed, and the tests that prove it.

**Audience:** you, rehearsing for a question like *"Walk me through how you'd match the same bottle of vodka sold by two different supermarkets under two different names."*

---

## 1. The problem, stated precisely

Ten NZ liquor retailers publish product data as JSON APIs, server-rendered HTML, embedded JS state, and Pjax fragments. None of them agree on:

- **Naming** — `"Absolut Vodka 700ml"` vs `"Absolut 700mL"` vs `"ABSOLUT VODKA 700 ML"`.
- **Units** — some embed volume in the name (`"12x330ml"`), some in a separate size field (`"24 x 330mL"`), some truncate it to a single letter (`"330c"`).
- **Categorisation** — `"Wine / Red Wine"` at one chain, `"red_wine"` at another, sometimes absent entirely.
- **Promo text** — `"3 for $50"`, `"2 for 1"`, `"Buy 2 Get 1 Free"`, `"Was $30 Now $25"` all mean different things and need different arithmetic.
- **Store scope** — some chains price identically everywhere; some (Countdown, the CityHive-platform chains) price per physical store, so the *same* SKU can legitimately have 90+ different prices.

Two distinct engineering problems hide inside "normalization," and it's worth naming them separately because the code solves them with different tools:

1. **Parsing** — turn one messy string into structured fields (`total_volume_ml`, `pack_count`, `abv_percent`, `brand`, `category`, `is_sugar_free`, and cleaned promo numbers). This is regex-and-lookup-table work, done independently per product, per scrape.
2. **Entity resolution (matching)** — decide whether two *already-parsed* records, scraped from two different chains, describe the same physical product. This is a deterministic hashing problem, done once parsing has produced the inputs it needs.

The rest of this document follows that split: §2–4 is parsing, §5 is matching, §6 is what happens once matching succeeds, §7 is three real scraper stories that show both halves under real HTML, §8 is limitations, §9 is a rehearsal Q&A set.

---

## 2. Where this code lives

| Concern | File |
|---|---|
| Volume/pack/ABV/brand/category/sugar-free parsing | `api/app/services/parser_utils.py` (692 lines) |
| CityHive truncated-size-code fix | `parser_utils.py::expand_cityhive_size_codes` |
| Canonical ID (entity resolution) | `api/app/services/canonical.py` (151 lines) |
| Money rounding + value metrics (price/100ml, price/standard drink) | `api/app/services/pricing.py` |
| Promo string parsing (deals, dates, member-only) | `api/app/services/promo_utils.py` (422 lines) |
| Shared scraper base — wires parsing + hashing + upsert together | `api/app/scrapers/base.py` (552 lines) |
| Per-chain scrapers (10 of them) | `api/app/scrapers/*.py` |
| Where a matched canonical group is actually queried | `api/app/services/product_detail.py::fetch_product_detail` |
| Offline re-hash tool | `api/scripts/backfill_canonical_ids.py` |
| Test coverage | `test_canonical.py`, `test_parser_utils.py`, `test_services_parser_utils.py`, `test_scraper_parser_utils.py`, `test_scraper_promo_utils.py`, `test_services_pricing.py`, `test_scraper_all_chains.py` |

> There is a second, unrelated `api/app/store_scrapers/` package. It scrapes store *locations* (addresses/coordinates), not product data, and — as of this snapshot — isn't wired into the live worker/routes; only its own test imports it. Don't confuse it with the pipeline below if it comes up.

---

## 3. Parsing: turning one string into structured fields

### 3.1 Volume and pack count — `parse_volume`

Four regexes, tried in a fixed order, each covering a distinct way retailers write quantity:

```python
VOLUME_PATTERN = re.compile(
    r"(?P<count>\d+)\s*[x×]\s*(?P<unit>\d+(?:\.\d+)?)\s*(?P<measure>ml|cl|l|ltr|litre|litres|liters)\b",
    re.IGNORECASE,
)  # "12x330ml", "12 × 330ml"

PACK_VOLUME_PATTERN = re.compile(
    r"(?P<count>\d+)\s*(?:pk|pack)\s+(?P<unit>\d+(?:\.\d+)?)\s*(?P<measure>ml|cl|l|ltr|litre|litres|liters)\b",
    re.IGNORECASE,
)  # "12pk 250ml Cans"

SINGLE_VOLUME_PATTERN = re.compile(
    r"(?P<unit>\d+(?:\.\d+)?)\s*(?P<measure>ml|cl|l|ltr|litre|litres|liters)\b",
    re.IGNORECASE,
)  # "700ml" -> pack_count=1

PACK_ONLY_PATTERN = re.compile(
    r"(?P<count>\d+)\s*(?:pk|pack)?\s*(?:bottles?|btls?|cans?|pack|pk)\b",
    re.IGNORECASE,
)  # "12 Bottles" - no volume at all
```

`parse_volume` (`parser_utils.py:60-89`) tries them in that exact order and returns on the first hit. Unit conversion is simple multiplication: `l` → ×1000, `cl` → ×10, `ml` → ×1 (`parser_utils.py:68,75,81`). Litre spelling variants (`litre/litres/liter/liters/ltr`) are normalised to `l` *before* any pattern runs, so one set of patterns covers all spellings.

The last pattern, `PACK_ONLY_PATTERN`, is the interesting design decision: when a name says `"12 Bottles"` with **no volume anywhere**, the parser assumes **330ml**, the standard NZ beer bottle/can size, and only if `count >= 2` — a guard against a stray unrelated digit in the name matching as a fake pack count of 1.

```python
match = PACK_ONLY_PATTERN.search(normalized)
if match:
    count = int(match.group("count"))
    if count >= 2:  # Avoid matching stray single digits
        return ParsedVolume(pack_count=count, unit_volume_ml=330.0, total_volume_ml=count * 330.0)
```

This is a real, named assumption — flag it as one if asked "what's a fragile part of this system." It's correct for beer/RTD packs and silently wrong if it ever fires on, say, a boxed wine case.

**Separately**, `Scraper.build_product_dict()` (`base.py:203-219`) applies a *second*, narrower default: if a name has no volume information at all, wine-category products default to **750ml/pack=1** and spirit-category products default to **700ml/pack=1** — the two most common single-bottle sizes in those categories. This only fires when parsing found nothing, and it's category-gated, unlike the 330ml pack-count fallback above which is category-agnostic.

### 3.2 The CityHive truncated-unit bug — a real production fix

Two chains run on the CityHive platform (Bottle-O, Liquor Centre). Their product names truncate the volume unit to a single letter: `"330c"` (can), `"330b"` (bottle), `"700m"` (truncated "ml"). None of the four patterns above recognise that — which left roughly **7,000 products with `NULL total_volume_ml`** before the fix (documented directly in the code, `parser_utils.py:27-31`).

The fix is a pre-pass that runs *before* `parse_volume`:

```python
_CITYHIVE_TRUNCATED_UNIT = re.compile(r"(\d)(?:[cbm])\b", re.IGNORECASE)

def expand_cityhive_size_codes(text: str) -> str:
    """
    "Carlsberg 330c"           -> "Carlsberg 330ml"
    "Cruiser Cool Lime 1x275b" -> "Cruiser Cool Lime 1x275ml"
    "Deanston 700m"            -> "Deanston 700ml"
    """
    return _CITYHIVE_TRUNCATED_UNIT.sub(r"\1ml", text)
```

The word-boundary anchor (`\b`) is load-bearing: it's what stops this from mangling an ABV like `"3.6%"` or a whisky age statement like `"16yo"` — neither has a bare `c`/`b`/`m` immediately after a digit at a word boundary in the wrong shape. This is a good "tell me about a bug you fixed" story: a single-letter suffix ambiguity that silently dropped structured data for two whole retailers, caught by staring at NULL-rate stats per chain rather than by an exception.

### 3.3 ABV extraction

```python
ABV_PATTERN = re.compile(r"(?<!\d)(?P<abv>\d{1,2}(?:\.\d+)?)\s*%")
```

The negative lookbehind `(?<!\d)` is the whole trick: without it, `"100% Natural"` would match `"00%"` as the ABV group inside `"100%"` (a 1-2 digit group can match the trailing two digits of a 3-digit number). `TestABVFalsePositives::test_100_percent_natural` and `test_200_percent_markup` lock this in as regression tests.

### 3.4 Brand inference — `infer_brand`

Two-tier strategy:

1. **Known-brand list.** `KNOWN_BRANDS` (`parser_utils.py:99-134`) is a curated ~120-entry list of real NZ liquor brands, compiled into word-boundary patterns and **sorted longest-first**. Sorting matters: `"Smirnoff Ice Raspberry 4x300ml"` must match `"Smirnoff Ice"` (a distinct product line with its own ABV/category) before the shorter `"Smirnoff"` pattern gets a chance to match — `test_smirnoff_ice_matches_before_smirnoff` proves this.
2. **Fallback heuristic** for anything not in the list (`parser_utils.py:229-256`): strip leading descriptor words (`premium`, `classic`, `reserve`, `gold`, …), then take 1-2 remaining words as the brand — but reject a second word if it's a wine-variety/spirit-type/beer-type/RTD word (a rejection set, `_FALLBACK_SECOND_WORD_REJECT`, `parser_utils.py:145-160`), which stops nonsense brands like `"Akarua Pinot"` (should be brand=`"Akarua"`) or `"1792 Small"` (should be brand=`"1792"`).

Word-boundary anchoring throughout is what prevents short brand tokens from matching as substrings of unrelated words — this is a whole cluster of regression tests worth knowing by name if asked about false positives:

| Test | What it guards against |
|---|---|
| `test_tui_does_not_match_tuition` | `"Tui"` (beer brand) inside `"Tuition"` |
| `test_db_does_not_match_database` | `"DB"` (beer brand) inside `"Database"` |
| `test_sol_does_not_match_absolut` | `"Sol"` (beer brand) inside `"Absolut"` |
| `test_ginger_beer_not_gin` | `"Gin"` (spirit type) inside `"Ginger Beer"` |
| `test_export_gold_not_port` | `"Port"` (wine type) inside `"Export Gold"` |
| `test_sale_item_not_ale` | `"Ale"` (beer type) inside `"Sale Item"` |
| `test_rummage_not_rum` | `"Rum"` (spirit type) inside `"Rummage"` |

And two that prove edge-case coverage rather than false-positive avoidance:

- `test_numeric_brand_names` — `"1800 Tequila Silver 700ml"` resolves a purely numeric token (`"1800"`) as the brand, and still classifies the category as `tequila`.
- `test_unicode_handling` — `"Matua Rosé 750ml"` is accepted whether the category resolves via the `"rose"` keyword or Matua's brand→category mapping; accented characters aren't normalised before matching, which the test documents rather than hides.

### 3.5 Category inference — `infer_category`

Ordered, longest-keyword-wins matching against `CATEGORY_KEYWORDS` (`parser_utils.py:163-206`), from most specific (`vodka`, `champagne`, `ipa`) down to broadest (`beer`, `wine`, `spirits`, `mixer`, `non_alcoholic`). A match is only trusted if the winning keyword is longer than 4 characters (`parser_utils.py:500`) — short accidental matches fall through instead of being trusted.

The one genuinely clever bit: `has_alcohol_indicator` (`parser_utils.py:478-485`) reclassifies a `mixer` match as `rtd` (ready-to-drink, i.e. an alcoholic pre-mix) whenever an ABV%, or the words `"alc"`/`"spiked"`/`"hard"`, is also present. Without this, `"Vodka Lime & Soda 7% RTD"` would classify as a plain non-alcoholic mixer just because "soda" is a mixer keyword — `test_infer_mixer_vs_rtd` is the regression test.

When keyword matching is inconclusive, `BRAND_CATEGORY_MAP` (`parser_utils.py:262-462`, e.g. `"guinness": "stout"`, `"steinlager": "beer"`) is consulted as a fallback. A separate `CATEGORY_HIERARCHY` (`parser_utils.py:520-540`, e.g. `ipa → beer`, `bourbon → whisky`) exists purely for UI category rollups and is **not** consulted by the canonical hash — worth stating explicitly, since it's an easy thing to assume incorrectly.

### 3.6 Sugar-free detection

Keyword list (`"sugar free"`, `"zero sugar"`, `"low carb"`, `"no carbs"`, …), word-boundary compiled — same false-positive discipline as brand matching. `TestDetectSugarFree` proves `"Sugar Loaf Vineyard Pinot Noir"` and `"Carbine Stout 440ml"` do **not** trip sugar-free detection, because `"sugar"`/`"carb"` only appear as substrings of unrelated words (`Sugarloaf`, `Carbine`).

One brand-level override exists: `_SUGAR_FREE_BRANDS = {"clean collective"}` — a brand whose entire range is sugar-free even when an individual product's name doesn't say so.

### 3.7 Display formatting is a separate, cosmetic concern

`format_product_name` (`parser_utils.py:557-657`) title-cases names and de-duplicates repeated brand/region words for display (`"stoneleigh marlborough stoneleigh sauvignon blanc marlborough"` → `"Stoneleigh Sauvignon Blanc Marlborough"`). This runs **after** matching, purely for the UI, and is not part of the hash — it's a common trap to conflate "the name we show" with "the name we match on," and this codebase keeps them genuinely separate.

---

## 4. Money and promo normalization

This is a distinct sub-problem: after volume/brand/category parsing gives you *what* the product is, you still need to know *what it costs* — and promo text is its own miniature parsing problem.

### 4.1 Money rounding — `pricing.py`

Every price is forced through exact decimal rounding before it's ever compared or persisted:

```python
def normalize_money(value: Decimal | float | int | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```

Note the `Decimal(str(value))` — converting through `str()` rather than passing a `float` straight into `Decimal()` avoids binary floating-point artifacts (`Decimal(0.1)` is not exactly `0.1`; `Decimal(str(0.1))` is). This is called from every scraper's money-normalisation step (`base.py::_normalize_product_money`) and is the reason `Price.price_nzd`/`promo_price_nzd` are `Numeric(10,2)` columns, not floats, in the schema.

`compute_pricing_metrics` derives the two comparison metrics shown in the UI:

```python
STANDARD_DRINK_FACTOR = Decimal("78.9")   # NZ standard drink = 10g alcohol; ethanol density 0.789 g/ml
                                            # -> 0.789 / 0.01 = 78.9

price_per_100ml = price / (volume_ml / 100)
standard_drinks = (volume_ml / 1000) * (abv_percent / 100) * 78.9
price_per_standard_drink = price / standard_drinks
```

`test_services_pricing.py::TestStandardDrinkFactor` locks the `78.9` constant in directly, so a reviewer can verify the physical-constant derivation without re-deriving it from scratch.

### 4.2 Promo string parsing — `promo_utils.py`

This is where raw retailer promo text (badges, "was/now" pairs, deal strings) gets turned into structured numbers, and it's the part of the pipeline with the most genuine, interview-worthy ambiguity.

**`parse_promo_price`** (`promo_utils.py:31-65`) — pulls the *first* number out of a string via `r'\$?\s*([\d]+\.?\d*)'`. That's deliberately naive: `parse_promo_price("Was $30 Now $25")` returns **30.0**, not 25 — the first number, not the current one. This is documented directly in the test:

```python
("Was $30 Now $25", 30.0)   # test_price_extraction — comment: "Returns first price found"
```

The reason this is safe in practice is that no caller trusts `parse_promo_price` blindly on mixed "was/now" text — `extract_promo_info` (the generic promo-node extractor most scrapers call, `promo_utils.py:295-411`) instead reads was-price and current-price from *separate* DOM nodes when both exist, and falls back to `parse_promo_price` only on genuinely single-number badge text.

**`parse_multi_buy_deal`** (`promo_utils.py:68-137`) tries three shapes in order:

```python
# "3 for $50" -> {quantity: 3, total_price: 50.0, unit_price: 16.67}
r'(\d+)\s*for\s*\$?\s*([\d]+\.?\d*)'

# "2 for 1" -> {quantity: 2, total_price: 1.0, unit_price: 0.5}
r'(\d+)\s*for\s*(\d+)'

# "Buy 2 Get 1 Free" -> {quantity: 3, total_price: None, unit_price: None}
r'buy\s*(\d+)\s*get\s*(\d+)(?:\s*free)?'
```

The second pattern is the interview talking point: `"2 for 1"` is genuinely ambiguous English. It's colloquially "buy one, get one free" (a discount-on-quantity promo), but the parser reads it literally as "2 items, total price $1" — because the same regex shape also has to catch a real "$1 multi-buy" deal, and there's no way to distinguish the two from the string alone without extra context (e.g. comparing against the regular per-item price). `test_x_for_y_deals` locks in the literal-price interpretation as the current, known-imperfect behaviour — a good example of "here's a design decision I'd revisit with more data" rather than a bug nobody noticed.

**`parse_promo_end_date`** (`promo_utils.py:140-237`) strips `\$\d+(?:\.\d+)?` *before* handing text to `dateutil`'s fuzzy date parser — otherwise a string like `"2 for $36"` risks being fuzzy-parsed as a date (`test_price_text_not_parsed_as_date`). It also rejects any parsed date more than 366 days in the future as an obvious misparse (`test_far_future_date_rejected`) — a sanity bound against a stray number being read as a year.

**`detect_member_only`** (`promo_utils.py:240-261`) matches against `["club", "clubcard", "member", "members", "onecard", "loyalty", "rewards"]`, word-boundary anchored — `test_cardboard_not_member`, `test_nightclub_not_member`, and `test_gift_card_not_member` all prove the anchoring stops those keywords matching as substrings of unrelated words (`Cardboard`, `Nightclub`, `Gift Card`).

**`extract_promo_info`** only accepts an extracted promo price if it's strictly less than the current price (`promo_utils.py:385`) — a promo can never make a price look *higher*, which guards against DOM-selector mismatches silently swapping was/now values.

---

## 5. The canonical ID: the actual matching key

Everything above produces structured fields for **one listing at one chain**. This section is where two *separately scraped* listings get declared "the same physical product."

### 5.1 The hash

```python
_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

def compute_canonical_id(
    *, name=None, brand, total_volume_ml, pack_count,
    abv_percent=None, category=None, is_sugar_free=False,
) -> uuid.UUID | None:
    del abv_percent, category  # accepted for call-site compat; never hashed

    if total_volume_ml is None or pack_count is None:
        return None

    resolved_brand = brand
    if name:
        inferred = infer_brand(name)   # always re-infer from name, may override caller's brand
        if inferred:
            resolved_brand = inferred
    if not resolved_brand:
        return None

    variant = _extract_variant(name, resolved_brand) if name else ""

    key = "|".join([
        resolved_brand.strip().lower(), variant,
        str(total_volume_ml), str(pack_count), str(bool(is_sugar_free)),
    ])
    return uuid.uuid5(_NAMESPACE, key)
```

**The matching key is: `brand | variant | total_volume_ml | pack_count | is_sugar_free`.** Two listings from different chains get the same canonical UUID iff all five normalise identically. It's `uuid.uuid5` — deterministic, no randomness, no state, no database lookup required to compute; the same inputs always produce the same UUID anywhere it's called (worker, API, offline backfill script).

### 5.2 Variant extraction — isolating "what makes this SKU different from other bottles of the same brand+size"

```python
def _extract_variant(name: str, brand: str) -> str:
    s = name.lower()
    s = s.replace(brand.strip().lower(), "", 1)   # strip brand
    s = _VOLUME_RE.sub("", s)                     # strip volume ("700ml", "12x330ml")
    s = _PACK_RE.sub("", s)                       # strip pack words ("12 pack", "cans")
    s = _ABV_RE.sub("", s)                        # strip ABV ("40%")
    s = _NOISE_RE.sub("", s)                      # strip noise ("premium", "classic", "nz", ...)
    s = _MULTI_SPACE.sub(" ", s).strip()
    return _normalize_variant(s)                  # drop leading/trailing base-type words
```

```
"Absolut Vodka Citron 700ml"            → "citron"
"Absolut Passionfruit 700mL"            → "passionfruit"
"Heineken Lager 330ml 12 Pack"          → ""
"Jack Daniel's Tennessee Whiskey 700ml" → "tennessee"
```

`_normalize_variant` additionally collapses an all-base-type-word variant to `""` (e.g. bare `"Vodka"` after everything else is stripped) so `"Absolut Vodka 700ml"` and `"Absolut 700ml"` land on the same key instead of differing by a leftover `"vodka"` token.

### 5.3 Why `category` and `abv_percent` are deliberately excluded

This is the single most interview-relevant design decision in the whole pipeline, and it's documented in three places that all agree: the `compute_canonical_id` docstring, `test_category_does_not_affect_hash` / `test_abv_does_not_affect_hash`, and the backfill script's own comment (`backfill_canonical_ids.py:123-125`).

> Chains use incompatible category vocabularies (`"Wine / Red Wine"` vs `"red_wine"`) and inconsistently embed ABV in product names. Including either field in the hash **fragmented otherwise-identical SKUs into different canonical IDs** — a real false-negative bug that shipped and got fixed by removing fields from the key, not by adding more parsing.

That's a genuinely counterintuitive lesson worth being able to state out loud: *more signal in a matching key isn't automatically better if that signal is noisier across your data sources than the thing you're trying to match on.* The fields kept in the key (`brand`, `variant`, `total_volume_ml`, `pack_count`, `is_sugar_free`) were chosen because they're the fields retailers actually agree on once parsed, not because they're intrinsically "more important" attributes of the product.

`is_sugar_free`, notably, *is* kept — because it's a real, intentional product differentiator (a sugar-free variant is a genuinely different SKU, not noise), proven by `test_sugar_free_does_split_hash`: `"Coca-Cola 1.5L"` and `"Coca-Cola Zero 1.5L"` deliberately get **different** canonical IDs.

### 5.4 What happens when matching can't run

`compute_canonical_id` returns `None` — not a fallback guess — whenever `total_volume_ml`, `pack_count`, or a resolvable brand is missing (`test_missing_required_fields_returns_none`). An unmatchable product stays in the catalogue as its own row with `canonical_product_id = NULL`; it's simply excluded from cross-chain comparison rather than being force-matched into a possibly-wrong group. This is the conservative choice: false negatives (missed matches) are treated as acceptable; false positives (two different products shown as "the same") are not.

### 5.5 `attach_canonical_id` — always re-run, never trusted from before

```python
def attach_canonical_id(product_data: dict) -> dict:
    product_data["canonical_product_id"] = compute_canonical_id(
        name=product_data.get("name"), brand=product_data.get("brand"),
        total_volume_ml=product_data.get("total_volume_ml"),
        pack_count=product_data.get("pack_count"),
        is_sugar_free=bool(product_data.get("is_sugar_free", False)),
    )
    return product_data
```

Called on **every** upsert, unconditionally overwriting any prior value (`test_overwrites_existing_canonical`). The stated rationale: this makes matcher-logic improvements self-healing — a matcher-quality fix in `canonical.py` corrects every product's grouping on its very next nightly scrape, with no separate migration or backfill required for the live path (the offline `backfill_canonical_ids.py` script exists for re-hashing without waiting for the next scrape, e.g. right after deploying a matcher fix).

---

## 6. Where the matched result actually gets used

`canonical_product_id` isn't a global "canonical products" table — there isn't one. It's a **nullable, partially-indexed grouping column** directly on `products`:

```python
Index("ix_product_canonical", "canonical_product_id",
      postgresql_where=text("canonical_product_id IS NOT NULL"))
```

A partial index, because most of the index's value is in the frequent "give me everyone sharing this ID" lookup — indexing the (very common) `NULL` rows would be pure overhead.

The one place that lookup happens is `fetch_product_detail` (`api/app/services/product_detail.py:86-134`): given one `Product.id`, it queries every other `Product` row sharing the same `canonical_product_id`, joined to `Price`/`Store`, filtered to `Store.sells_alcohol.is_(True)`, ordered by effective price. Then:

```python
seen_chains: set[str] = set()
for compared_product, compared_price, compared_store, distance in rows:
    if compared_store.chain in seen_chains:
        continue
    seen_chains.add(compared_store.chain)
    cross_chain_prices.append(build_cross_chain_price(...))
```

**Deduplication by `store.chain`** — this is deliberate and easy to miss: even though the query can return many `Store` rows per chain (per-store pricing chains have dozens of matching rows), the response surfaces at most **one, cheapest, matching price per competing chain**. This is exactly the "same product, different retailer, apples-to-apples" comparison the product exists to answer — a user comparing "this bottle of Absolut near me" doesn't want to see the same Countdown listing 12 times because 12 different Countdown branches stock it; they want one row per competing retailer.

---

## 7. Three scrapers, three shapes of the same problem

### 7.1 Countdown — per-store JSON API, chain-wide product identity

Woolworths NZ genuinely prices differently store-to-store, so `CountdownAPIScraper` sets `_sweep_per_store = True` and iterates every store, switching the session's fulfilment address (`PUT /api/v1/fulfilment/my/pickup-addresses`) before each search pass. `_parse_product` appends the API's own `size_info["volumeSize"]` field (e.g. `"24 x 330mL"`) onto the name string before running it through the same `parse_volume` used everywhere else — reusing the shared parser rather than trusting the API's structured size field directly, since that field's format also varies. It detects "not stocked at this store" via price sentinels (`0` or `99999.99`), and promo detection requires both `isSpecial` **and** `sale_price < price` — never trusting a single boolean flag alone.

### 7.2 Super Liquor — chain-wide HTML, specials merged across pages

A more conventional chain-wide scraper (one price per SKU, not per store), scraping paginated category pages with `selectolax`. The interesting part: this chain runs a separate `/super-specials` landing page that isn't guaranteed to repeat on the item's normal category page later. The scraper visits `/super-specials` *first*, caches the lowest observed price per product, and when it later visits the item's regular category page (which may show no promo badge at all), it applies the cached special price as `promo_price_nzd` if it beats the regular-page price. This is how a sitewide promo gets correctly attached to a SKU that doesn't repeat the promo marker on every page it appears on — a cross-page join done in application code because the source site doesn't expose that relationship structurally.

### 7.3 Bottle-O — CityHive HTML, a real per-store duplication bug and its fix

The most instructive story in the codebase. Bottle-O runs ~90 franchise stores on the CityHive platform. Each product card ("talker") in the DOM carries `id="line_<hex>"` — which looks like a natural unique ID, but isn't: **it's a per-store inventory-line ID**, not a chain-wide product ID. An earlier version of the scraper used it as `source_product_id`, and because `Product` identity is `(chain, source_product_id)`, that meant the *same physical SKU got inserted once per store* — up to ~90 duplicate `Product` rows for one bottle of vodka.

The fix, documented directly in the source:

```python
# Product URL - the chain-wide product slug lives in the <a href>.
# The element's id="line_<hex>" is a per-store inventory line ID and
# MUST NOT be used as source_product_id (it caused the duplicate-product
# bug where the same SKU was inserted once per store).
```

`source_product_id` now comes from the chain-wide URL slug in the product's `<a href>`; store identity travels separately as a `store_identifier` field on the same dict. A talker with no usable `href` is skipped entirely rather than upserted under a synthetic ID (`test_skips_talker_without_usable_href`). Two regression tests pin the fix directly: `test_same_sku_different_stores_shares_source_id` and `test_bottle_o_two_stores_one_product_identity` both assert that scraping the same product from 2-3 different store pages produces **one shared `source_id`** with **distinct `store_identifier`s** — one `Product` row, N `Price` rows, exactly the intended shape.

This is a great "describe a bug you fixed and how you prevented recurrence" answer: wrong assumption about what a DOM `id` attribute actually scopes to, caught by a duplication symptom, fixed by finding the *actually* chain-wide identifier, locked in with a test that would fail immediately if the regression ever came back.

---

## 8. Limitations and honest talking points

Be ready to name these unprompted — it reads better than waiting to be asked "what would you improve."

- **`"2 for 1"` ambiguity** (§4.2) — resolved as a literal price interpretation, not a "buy one get one free" discount, because the regex can't tell the two apart from text alone.
- **`PACK_ONLY_PATTERN`'s 330ml assumption** (§3.1) — correct for beer/RTD, silently wrong if it ever fires on something like a wine multi-pack.
- **No confidence score.** Matching is binary — same canonical ID or not — with no precision/recall measurement in production. `test_...` files cover known cases, but there's no labelled-pairs dataset measuring real-world false-positive/false-negative rates at scale (this is explicitly named as a next step in the handbook's Q29 and worth repeating here: *"build a labelled pair dataset, measure precision/recall by category and brand, inspect high-confidence collisions, monitor canonical groups with implausibly different prices/names/volumes"*).
- **Accented characters aren't normalised** before keyword matching (`test_unicode_handling` documents rather than fixes this) — a category or brand match can depend on whether the source text used `é` vs `e`.
- **Brand-substring stripping is a single `.replace(brand, "", 1)`** in `_extract_variant` — if the brand string doesn't appear verbatim in the name (casing aside) because a scraper's inferred `brand` differs slightly from the name's actual text, the variant extraction silently doesn't strip it, and the leftover brand text becomes noise in the variant.
- **The 330ml default and the wine/spirit 750/700ml defaults are two separate, independently-triggered fallbacks** (`parse_volume`'s `PACK_ONLY_PATTERN` vs. `build_product_dict`'s category-based default) — easy to conflate as "one fallback," but they're different code paths with different trigger conditions.

---

## 9. Rehearsal Q&A

**Q1. Walk me through what happens between scraping a product and it being comparable to a product from a different chain.**
A scraper produces a raw name/price string. `parser_utils` extracts structured fields from the name (volume, pack, ABV, brand, category, sugar-free) via ordered regex passes and lookup tables. `pricing.py`/`promo_utils.py` normalise the price and promo text to exact decimals and structured deal info. `canonical.py::compute_canonical_id` then hashes `brand | variant | total_volume_ml | pack_count | is_sugar_free` into a deterministic UUIDv5, re-inferring brand from the name so the hash is stable regardless of what a particular chain stored as `brand`. That UUID is written to `Product.canonical_product_id`. Any other product sharing that UUID is the same physical SKU from a different retailer, queryable via a single partial index.

**Q2. Why exclude category and ABV from the matching key when they seem like obviously relevant product attributes?**
Because they're *less* reliable across sources than the fields kept. Category vocab is chain-specific and sometimes missing; ABV is inconsistently embedded in product names. Including either field turned same-product listings from different chains into different canonical IDs — a real shipped false-negative bug. The fix was removing signal from the key, which is the counterintuitive but correct move when a field is noisier across your sources than the thing you're actually trying to identify.

**Q3. What's the difference between `category` (excluded from matching) and `CATEGORY_HIERARCHY` (`ipa → beer`)?**
`category` is a per-listing display/filter attribute, inferred independently per chain and *not* part of cross-chain identity. `CATEGORY_HIERARCHY` is a separate UI concern — rolling up specific categories to broad ones for filtering — and isn't consulted by the hash either. Neither participates in deciding "is this the same product," which is driven only by brand/variant/volume/pack/sugar-free.

**Q4. How do you avoid false matches (two different products getting the same canonical ID)?**
Conservatively: `compute_canonical_id` returns `None` rather than guessing whenever volume, pack count, or brand can't be resolved — an unmatched product just doesn't get grouped, rather than being force-matched. Word-boundary-anchored regexes throughout parsing (brand, category, sugar-free, member-only detection) prevent short tokens matching as substrings of unrelated words (`"Tui"` inside `"Tuition"`, `"Rum"` inside `"Rummage"`). And `is_sugar_free` is deliberately *kept* in the hash specifically because a sugar-free variant is a real, distinct SKU that should NOT collapse into its regular counterpart.

**Q5. How do you avoid false negatives (the same product NOT matching across chains)?**
By keeping the hash key to only the fields that parse consistently, re-inferring brand from the name every time rather than trusting each chain's stored `brand` field, stripping noise words (`"premium"`, `"classic"`, `"nz"`) and generic base-type words (`"vodka"`, `"lager"`) from the variant so cosmetic differences in how a chain phrases the same product don't fragment the match, and fixing known unit-format gaps (the CityHive truncated-suffix bug) that were silently leaving ~7k products unparseable and therefore unmatchable.

**Q6. Tell me about a real bug in this pipeline and how it was found and fixed.**
Two good answers, pick based on what's being probed:
- *Duplication bug* (Bottle-O, §7.3): using a per-store DOM element ID as if it were a chain-wide product ID caused the same SKU to be inserted ~90 times, once per store. Fixed by deriving the ID from the chain-wide URL slug instead, with store identity carried as a separate field; locked in with two regression tests that assert one shared ID across multiple stores.
- *Parsing gap bug* (CityHive truncated units, §3.2): two chains truncated volume units to a single letter (`"330c"`), which none of the volume regexes recognised, silently leaving ~7,000 products with no volume data — and therefore unmatchable, since volume is a required hash input. Fixed with a targeted pre-expansion pass, anchored carefully enough not to also mangle ABV percentages or whisky age statements.

**Q7. Why UUIDv5 specifically, and why a fixed namespace UUID?**
UUIDv5 is a deterministic, name-based hash (SHA-1 under the hood) — no randomness, no database round-trip, no coordination needed between the live scrape path and the offline backfill script to agree on an ID for the same inputs. The fixed namespace UUID is just a project-specific salt so Liquorfy's canonical IDs don't collide with UUIDv5s generated by an unrelated system using the same input strings.

**Q8. How would you measure whether the matcher is actually good, beyond unit tests?**
Unit tests prove specific known cases stay fixed; they don't measure real-world precision/recall. The next step (not yet built) would be a labelled pair dataset — human-verified "these two listings are/aren't the same product" — to measure precision and recall broken down by category and brand, plus a monitoring query for canonical groups whose members have implausibly different price, name, or volume, as a cheap proxy for likely false positives in production.

**Q9. Where in the database does a "canonical product" actually live?**
Nowhere, as its own table — there is no canonical-products table. `canonical_product_id` is a nullable UUID column directly on the per-chain `products` row, with a partial index (`WHERE canonical_product_id IS NOT NULL`) supporting the "find everyone else with this ID" query. Product identity for upsert purposes is `(chain, source_product_id)` — every chain owns its own row for the same physical product; the canonical ID is purely a grouping key layered on top, not a separate normalized entity.

**Q10. A per-store chain has 90 stores all stocking the same bottle. How does the product page avoid showing the same bottle 90 times when comparing across chains?**
Two separate deduplication mechanisms at two separate layers: same-chain, same-product store listings are handled upstream (nearest/cheapest-per-store selection in search); the cross-chain comparison query specifically de-duplicates by `store.chain` while iterating price-ordered results, keeping only the first (cheapest) match per competing chain — so a user sees at most one comparison row per retailer, regardless of how many of that retailer's branches carry the item.

---

## 10. One-page cheat sheet

```
PARSE (per listing, per chain)
  name string
    → parse_volume()        4 ordered regexes: NxM, "pk N", bare N, count-only(→330ml if ≥2)
    → expand_cityhive_size_codes()   pre-pass for "330c"/"330b"/"700m" (2 chains only)
    → extract_abv()          (?<!\d)\d{1,2}(\.\d+)?% -- lookbehind blocks "100%" false hit
    → infer_brand()          known-brand list (longest-first) → fallback heuristic
    → infer_category()       longest-keyword-wins → BRAND_CATEGORY_MAP fallback
                              mixer→rtd reclassify if ABV/alc/spiked/hard present
    → detect_sugar_free()    keyword list + brand override set
  price/promo string
    → normalize_money()      Decimal(str(x)).quantize(0.01, ROUND_HALF_UP)
    → parse_promo_price()    first number in string (naive; callers compare was/now separately)
    → parse_multi_buy_deal() "N for $X" / "N for M" / "Buy N Get M" -- 3 ordered patterns
    → parse_promo_end_date() strip $amounts first, then dateutil fuzzy parse, reject >366d out
    → detect_member_only()   word-boundary keyword match

MATCH (across chains)
  compute_canonical_id(brand, name, total_volume_ml, pack_count, is_sugar_free)
    re-infers brand from name (always, may override caller's brand)
    _extract_variant(): strip brand/volume/pack/ABV/noise, drop base-type-only leftovers
    key = brand|variant|total_volume_ml|pack_count|is_sugar_free   -- NOT category, NOT abv
    return uuid.uuid5(FIXED_NAMESPACE, key), or None if volume/pack/brand unresolved
  attach_canonical_id(): called on every upsert, always overwrites -- self-healing matcher fixes

USE
  Product.canonical_product_id: nullable UUID column, partial index (WHERE NOT NULL)
  fetch_product_detail(): join same canonical_product_id, sells_alcohol=True,
                           order by effective price, dedupe by store.chain
                           → at most one (cheapest) comparison row per competing retailer
```
