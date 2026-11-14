# Database Indexing & Performance — Interview Prep

> Companion to `LIQUORFY_INTERVIEW_HANDBOOK.md`. That doc covers Liquorfy end to end;
> this one goes deep on one axis — indexing and query performance — because it is
> the single topic most likely to get a multi-question follow-up chain in a
> backend/data interview. Every example is real: pulled from the actual Alembic
> migrations and `api/app/services/search*.py` in this repo, not invented for the
> doc. Where a concept is general CS knowledge rather than Liquorfy-specific, it's
> labelled **[General]**; where it's this codebase, it's labelled **[Liquorfy]**.

---

## 1. How indexes actually work **[General]**

An index is a separate, ordered data structure that trades write cost and storage
for read speed. Without one, satisfying a filter means a sequential scan —
Postgres reads every row and evaluates the predicate. An index lets Postgres
jump straight to matching rows (or a small candidate set) without touching the
rest of the table.

### B-tree (the default, and 90% of what you need)

- Balanced tree, O(log n) lookup, keeps keys sorted.
- Supports `=`, `<`, `<=`, `>`, `>=`, `BETWEEN`, `IN`, `ORDER BY`, and prefix
  `LIKE 'foo%'` (not `LIKE '%foo%'` — no leading wildcard).
- The only index type most engineers will ever explicitly reach for.

### Hash

- O(1) average lookup, but only supports `=`. No range queries, no sorting.
- Rarely worth it over B-tree in Postgres today — B-tree equality lookups are
  already fast, and hash indexes historically weren't WAL-logged (crash-unsafe)
  before Postgres 10. Mentioning this history is a good signal you understand
  *why* B-tree is the default, not just that it is.

### GiST (Generalized Search Tree) **[Liquorfy: `ix_stores_geog`]**

- A framework for building tree indexes over data that doesn't have a strict
  total order — geometric shapes, ranges, full-text vectors.
- Liquorfy uses it for PostGIS: `stores.geog` is a generated
  `geography(Point, 4326)` column with a GiST index, which is what makes
  `ST_DWithin` (radius search) and `ST_Distance` fast instead of a full table
  scan with per-row great-circle math.
- General interview framing: GiST answers "is this shape near/inside/overlapping
  that shape" efficiently; B-tree can't express that at all.

### GIN (Generalized Inverted Index) **[Liquorfy: `ix_products_name_trgm`, `ix_products_brand_trgm`]**

- Inverted index: maps each *component* of a value (array elements, JSONB keys,
  trigrams, tsvector lexemes) back to the rows containing it.
- Liquorfy uses `pg_trgm` GIN indexes on `lower(products.name)` and
  `lower(products.brand)` to accelerate case-insensitive substring search
  (`ILIKE '%term%'` / `LIKE` on a lowercased column). A plain B-tree can't help
  with a leading wildcard — trigram indexes break the string into 3-character
  chunks and index those, so a substring match becomes a lookup over the
  chunks the search term is made of.
- Slower to build and update than B-tree (GIN write amplification is a known
  cost); fine here because product catalog writes are batched nightly, not
  interactive.

### BRIN (Block Range Index) **[General, not currently used here]**

- Stores min/max per block range instead of a full per-row structure — tiny,
  cheap to maintain, good for huge tables where a column correlates with
  physical insertion order (e.g., a monotonically increasing `created_at` on
  an append-only log). Worth naming as the answer to "what if `price_history`
  grows to hundreds of millions of rows and per-row B-tree indexes get too
  large" — see §9.

---

## 2. Composite indexes, column order, and covering indexes **[General]**

A composite (multi-column) index is sorted first by column 1, then column 2
within each value of column 1, and so on. That ordering has real consequences:

- **Leftmost-prefix rule**: an index on `(a, b, c)` can serve queries filtering
  on `a`, on `a AND b`, or on `a AND b AND c` — but *not* on `b` alone or `c`
  alone. Put the column with equality filters and highest selectivity first,
  unless a specific range/sort pattern says otherwise.
- **Liquorfy example**: `ix_price_history_product_recorded` is
  `(product_id, recorded_at)`. Every real query is "history for this one
  product, ordered/filtered by time" — so `product_id` first lets Postgres
  jump to that product's slice, then walk `recorded_at` in already-sorted
  order for the range scan.
- **Covering index / index-only scan**: if every column a query needs (filter
  columns + selected columns) is present in the index, Postgres can answer
  the query from the index alone, skipping the heap (table) fetch entirely —
  visible in `EXPLAIN` as `Index Only Scan` instead of `Index Scan`. Requires
  the visibility map to be up to date (i.e., `VACUUM` has run), or Postgres
  still has to check heap visibility per row.

---

## 3. Partial indexes — Liquorfy's best interview story **[Liquorfy]**

A partial index only covers rows matching a `WHERE` clause on the index
definition. Three real examples from this repo, each solving a different
problem:

**a) `ix_price_promo_ends_at_partial`** — `prices(promo_ends_at) WHERE promo_ends_at IS NOT NULL`

```
The hourly promo-expiry cleanup filters:
  promo_ends_at IS NOT NULL AND promo_ends_at < now() AND promo_price_nzd IS NOT NULL
With no index, Postgres sequential-scans `prices`, which timed out under
degraded Supabase IO. Most rows never have a promo, so a full index on
promo_ends_at would mostly index NULLs — wasted space, wasted maintenance.
The partial index keeps only the rows that matter, small and fast.
```

Also created `CONCURRENTLY` (see §7) so the migration didn't lock writes on a
live table.

**b) `ix_product_canonical`** — `products(canonical_product_id) WHERE canonical_product_id IS NOT NULL`

Same shape: canonical IDs are only populated once entity resolution has run,
so most rows are NULL. Indexing only the resolved rows keeps the cross-chain
"same product at a different retailer" lookup cheap without paying for NULLs.

**c) Ingestion job scheduling — two partial indexes doing different jobs**

```sql
-- Only queued jobs are "ready to claim" — this index only needs to hold that slice
CREATE INDEX ix_ingestion_job_ready ON ingestion_jobs (available_at, created_at)
  WHERE status = 'queued';

-- Only running jobs can have an expired lease — same idea, different status
CREATE INDEX ix_ingestion_job_expired_lease ON ingestion_jobs (lease_expires_at)
  WHERE status = 'running';
```

This is a *job queue implemented on top of a normal table*: the worker polls
"give me the next queued job" and "find running jobs whose lease expired so I
can reclaim them." A full index on `status` would still make the worker scan
through `completed`/`failed`/`cancelled` rows it will never touch as the table
grows. Partial indexes make the index *shape match the access pattern*
instead of the schema.

**d) `uq_ingestion_job_dedupe_key`** — unique partial index, not just a
performance index: `ingestion_jobs(dedupe_key) WHERE dedupe_key IS NOT NULL`
enforces "at most one queued/running job per chain per night" (`dedupe_key =
nightly:{date}:{chain}`) while still allowing unlimited historical rows with
`dedupe_key = NULL`. A plain unique constraint couldn't do this — it would
either forbid multiple NULLs incorrectly interacting or require a NULL
sentinel hack. **This is a good answer to "have you used an index to enforce
a business rule, not just for speed."**

**General framing for the interviewer**: partial indexes are the right tool
whenever (1) queries only ever touch a well-defined subset of rows, and (2)
that subset is much smaller than the table. They shrink index size, speed up
writes to the excluded rows (nothing to update), and improve cache locality
for the included ones.

---

## 4. When materializing a CTE fixes the query plan **[Liquorfy — the deepest story in this doc]**

This is the single most interesting performance decision in the codebase, and
worth having a tight 90-second version ready.

**The problem.** `fetch_products` (`api/app/services/search.py`) supports a
free-text search *combined with* a nearby-location radius filter, plus a long
tail of other filters (category, ABV, pack size, price range) and an optional
"unique products, cheapest per store cluster" dedup mode. The natural
SQLAlchemy/SQL way to write "find products where name matches AND store is
nearby" is: build both predicates, `AND` them together, let the planner
figure out the join order.

**What went wrong.** Postgres's planner chose a *combined* plan — it picked
one predicate (often the geo one) to drive the scan and then filtered the
other predicate row-by-row, instead of independently reducing both to small
candidate sets first and joining those. On this schema (products × prices ×
stores, radius search + trigram search both selective on their own but not
combinable well by the planner's cost estimates) that produced a slow plan
even though both `ix_products_name_trgm` (GIN) and `ix_stores_geog` (GiST)
existed and were individually usable.

**The fix**, from `search.py`:

```python
matching_products_cte = (
    select(Product.id.label("id"))
    .where(func.lower(Product.name).like(pattern))
    .cte(name="matching_products")
    .prefix_with("MATERIALIZED")
)
filters.append(Product.id.in_(select(matching_products_cte.c.id)))

nearby_stores_cte = (
    select(Store.id.label("id"))
    .where(Store.geog.is_not(None))
    .where(func.ST_DWithin(Store.geog, user_point_geog, radius_m))
    .cte(name="nearby_stores")
    .prefix_with("MATERIALIZED")
)
filters.append(Store.id.in_(select(nearby_stores_cte.c.id)))
```

Two `MATERIALIZED` CTEs, each independently index-backed (one hits the GIN
trigram index, one hits the GiST geography index), each forced to actually
materialize its own small result set *before* the outer query joins them. The
`products.id IN (...)` / `stores.id IN (...)` predicates against those small,
pre-computed ID sets are cheap semi-joins.

**Why `MATERIALIZED` specifically matters**: as of Postgres 12, CTEs are
inlined into the surrounding query by default (the old "CTEs are always an
optimization fence" behavior went away). Inlining is usually *good* — it lets
the planner see through the CTE and pick a better global plan. Here it was
*bad*: inlining let the planner go back to the same problematic combined plan
this fix was written to avoid. `MATERIALIZED` opts back into the pre-12
optimization-fence behavior for these two CTEs specifically, trading planner
flexibility for a predictable, index-anchored plan.

**The honest trade-off** (this is the answer to "what's the downside"): you
are hand-overriding the planner. That's brittle — it should be justified by
`EXPLAIN ANALYZE` evidence (not guessed), and revisited if the data
distribution changes a lot or after a Postgres version upgrade changes the
planner's default heuristics. It's a targeted, evidence-based override on two
specific hot-path predicates, not a blanket "materialize everything" policy.

**Second half of the same fix**: comment in the code — *"Similarity is
computed only in SELECT for relevance sort, never as a predicate — predicate
use bypasses the trigram index."* `similarity(name, q) > threshold` as a
`WHERE` clause does not use the GIN trigram index the way `LIKE '%term%'`
does; only the `%`/`<->` trigram operators (and the `LIKE`/`ILIKE` operator
classes `pg_trgm` registers) are index-backed. So filtering uses `LIKE`
against the index, and similarity is computed only for rows that already
survived that filter, purely to rank them.

---

## 5. Window functions for dedup instead of `GROUP BY` **[Liquorfy]**

The `unique_products=true` search mode needs "one row per distinct product
(by name/pack/volume), the single best-ranked listing across all nearby
stores, plus two aggregate facts about the group (cheapest price in the
group, how many stores carry it)" — three different things from the same
partition, computed together:

```python
func.min(effective_price).over(partition_by=dedup_partition).label("min_eff_price"),
func.count().over(partition_by=dedup_partition).label("store_count"),
func.row_number().over(partition_by=dedup_partition, order_by=tuple(sort_order)).label("rn"),
```
then `WHERE rn == 1` in the outer query.

**Why not `GROUP BY`**: `GROUP BY` collapses rows and can only return
aggregates, not "the full row that happens to be the best one, plus
aggregates computed across its whole group." You'd need a self-join or a
correlated subquery to get "best row + group stats" with plain aggregation,
which is both harder to write correctly and typically slower. Window
functions compute the aggregate *per row within its partition* without
collapsing the rows, so you can filter afterward (`rn = 1`) and still have
every original column available. This is a strong general answer to "when do
you reach for a window function instead of `GROUP BY`."

**Stable tie-breakers matter**: `sort_order` always ends with
`Price.price_last_changed_at.desc(), Product.name.asc(), Price.id.asc()`.
Without a fully deterministic `ORDER BY`, `ROW_NUMBER()` can pick a different
"winner" row on every execution when there's a tie — which would make paginated
results shuffle between page loads and make the "cheapest nearby" badge
flicker. Always finish an `ORDER BY` used for `ROW_NUMBER()`/pagination with a
unique column as the final tie-breaker.

---

## 6. Reading `EXPLAIN (ANALYZE, BUFFERS)` **[General]**

The standard loop for diagnosing a slow query:

1. Run `EXPLAIN (ANALYZE, BUFFERS) <query>` — never just `EXPLAIN` alone for
   perf work; you need actual row counts and timings, not just estimates.
2. Read **bottom-up**: the innermost nodes execute first; a slow top-level
   number is explained by whatever's slow underneath it.
3. Compare **estimated rows vs. actual rows** at each node. A huge mismatch
   (planner expected 10, got 100,000) means stale or insufficient statistics
   (`ANALYZE` the table, maybe raise `default_statistics_target` on that
   column) — and a bad row estimate cascades into bad join-order and
   join-algorithm choices upstream.
4. Watch for `Seq Scan` on a large table where you expected an `Index Scan` —
   means either no usable index exists, the predicate can't use the index
   that exists (e.g., function on the column without a matching expression
   index, leading wildcard on a plain B-tree), or the planner decided a seq
   scan was cheaper anyway (common when the query needs a large fraction of
   the table — indexes only win when selective).
5. `Index Scan` vs `Index Only Scan`: the latter skips the heap fetch
   entirely if the index covers every needed column and the visibility map is
   current — meaningfully faster, worth designing composite indexes toward
   when a query is hot enough to matter.
6. `Nested Loop` vs `Hash Join` vs `Merge Join`: nested loop is fine (even
   best) when the outer side is small; bad when both sides are large and
   unindexed on the join key — that shows up as a huge inner-loop row count
   multiplied by outer rows.
7. `Buffers: shared hit=... read=...` tells you cache effectiveness — high
   `read` (disk) vs `hit` (shared_buffers cache) on a repeated query means
   the working set doesn't fit in cache, which is a capacity/config problem,
   not a query-shape problem.

---

## 7. Index creation cost and `CONCURRENTLY` **[General, Liquorfy example]**

`CREATE INDEX` takes a `SHARE` lock on the table for its duration — reads still
work, but writes block until it finishes. On a large, live table that can mean
minutes of blocked writes. `CREATE INDEX CONCURRENTLY` avoids that by scanning
the table twice without holding the blocking lock, at the cost of being slower
overall and not being usable inside a transaction block (Alembic migrations
normally run in one transaction; `h2c3d4e5f6g7_add_promo_ends_at_partial_index.py`
explicitly opens `op.get_context().autocommit_block()` to get around that).
Also worth knowing: a `CONCURRENTLY` build can fail partway and leave an
`INVALID` index behind, which needs to be dropped and retried — mention this
if asked "what can go wrong."

---

## 8. Indexes aren't free — the write-side and maintenance cost **[General]**

Every index on a table is extra work on every `INSERT`/`UPDATE`/`DELETE`
touching an indexed column, extra storage, and extra `VACUUM` work. This is
why:

- You don't index every column "just in case" — index for actual query
  patterns (`WHERE`, `JOIN ON`, `ORDER BY` columns that are genuinely
  selective), not defensively.
- Partial indexes (§3) are a direct answer to this cost — smaller index,
  cheaper maintenance, for tables where writes matter (Liquorfy's nightly
  ingestion writes thousands of price rows; an unnecessary index on a
  low-value column would slow that down for no read benefit).
- `GIN` indexes (trigram, JSONB) are notably more expensive to update than
  B-tree — fine for a catalog that's rewritten in a nightly batch, would be a
  real cost on a table with constant interactive writes.
- Bulk-loading a large new dataset is often faster as: drop indexes → bulk
  `COPY`/insert → rebuild indexes, rather than paying per-row index
  maintenance during the load. Good to know exists even if not used here.

---

## 9. Full table-by-table index inventory **[Liquorfy — for the schema walkthrough question]**

| Table | Indexes / constraints | Why |
|---|---|---|
| `stores` | unique `(chain, name)`, unique `(chain, api_id)`, `ix_store_chain`, GiST on `geog` | chain filtering; dedupe on ingest; radius search |
| `products` | unique `(chain, source_product_id)`, `ix_product_chain`, GIN trigram on `lower(name)`, partial GIN trigram on `lower(brand) WHERE brand IS NOT NULL`, partial `ix_product_canonical WHERE canonical_product_id IS NOT NULL` | chain-scoped upsert; substring search; cross-chain matching only where resolved |
| `prices` | unique `(product_id, store_id)`, `ix_price_product_id`, `ix_price_store_id`, `ix_price_price_nzd`, `ix_price_promo_price_nzd`, `ix_price_last_changed`, `ix_price_last_seen`, partial `ix_price_promo_ends_at_partial WHERE promo_ends_at IS NOT NULL` | one current offer per product/store; FK join speed; price-range filters; promo cleanup |
| `price_history` | `ix_price_history_product_recorded (product_id, recorded_at)`, `ix_price_history_recorded_at` | append-only audit trail, always queried per-product-over-time |
| `ingestion_runs` | `ix_ingestion_run_chain_status (chain, status)`, `ix_ingestion_run_chain_started (chain, started_at)` | "is chain X currently running / when did it last run" |
| `ingestion_jobs` | partial `ix_ingestion_job_ready WHERE status='queued'`, partial `ix_ingestion_job_expired_lease WHERE status='running'`, unique partial `uq_ingestion_job_dedupe_key WHERE dedupe_key IS NOT NULL`, check constraints on status/attempt_count/max_attempts | durable job queue built on a normal table — indexes shaped to the polling access pattern, not the schema |
| `product_views` | PK on `product_id`, `ix_product_views_count` | one row per product, popularity sort |
| `price_alerts` | `ix_price_alert_user_active (user_id, active)`, `ix_price_alert_product_active (product_id, active)`, positive-threshold check | "this user's active alerts" and "which active alerts watch this product" — both hot paths after ingestion |

**Pattern to call out explicitly if asked "what's the design philosophy
here":** every index maps to a *named, real query* — the FK indexes exist
because `prices` is joined to `products`/`stores` on every search; the
composite `(chain, status)` indexes exist because the scheduler and worker
literally query "jobs for chain X in state Y"; the partial indexes exist
because the underlying access pattern only ever touches a slice of the table.
None of them were added speculatively — see `a1b2c3d4e5f6_add_performance_indexes.py`,
whose own migration docstring labels each index Critical/High/Medium by
actual query frequency, not by "seems reasonable."

---

## 10. Caching as the layer *above* indexing **[Liquorfy]**

Indexing makes a query fast; caching skips the query entirely. Liquorfy layers
both: `get_store_ids_within_radius` (`search_support.py`) wraps the
GiST-backed `ST_DWithin` query in `cached_json(...)`, keyed by
`stores_nearby:{lat}:{lon}:{radius_km}` rounded to fixed precision, with a
short TTL from config. This is the *no-text-search* fast path — same nearby
stores are requested repeatedly as a user pans/filters without changing
location, so the cache absorbs that instead of re-running even a fast
indexed geo query every time.

**Important distinction to make in an interview**: the text-search path
(§4) does *not* use this cache — it needs a fresh materialized CTE join per
distinct search term, which isn't cacheable the same way (too many distinct
`(term, lat, lon, radius)` combinations for a short-TTL cache to help much).
Knowing *where* caching pays off vs. where indexing has to carry the whole
load — and why — is a stronger answer than "we cache everything."

Also worth stating as a design principle: Redis failures here don't block
reads — the API falls back to a live (indexed) Postgres query. Cache is a
speed optimization on top of a correct, indexed baseline, not a dependency
the read path can't survive without.

---

## 11. Likely interview questions with model answers

**Q: Walk me through choosing an index type for a new query.**
A: Start from the actual predicate shape. Equality/range on a scalar column →
B-tree, almost always. Substring/fuzzy text match → trigram GIN. Geometric
containment/proximity → GiST. Then check selectivity — if the predicate only
excludes a small fraction of rows, an index won't help and the planner will
correctly ignore it in favor of a seq scan. Then check whether the access
pattern only ever touches a subset of rows (→ partial index) and whether the
query filters on more than one column together (→ composite, ordered by
leftmost-prefix usage). Verify with `EXPLAIN ANALYZE` against production-like
data volume, not a near-empty dev database — plans change with table size.

**Q: You added an index and the query didn't get faster. Why?**
A: Several possibilities: the predicate doesn't match the index shape (e.g.,
a function applied to the column with no matching expression index, or a
leading-wildcard `LIKE` against a plain B-tree); statistics are stale so the
planner doesn't know the index would help (`ANALYZE`); the table/result set
is small enough that a seq scan is genuinely cheaper; or — the CTE story in
§4 — multiple individually-index-backed predicates get combined into a plan
that doesn't actually use either index efficiently, which needs a plan-shape
fix (materialization, restructuring the query), not another index.

**Q: How do you decide *not* to add an index?**
A: Low selectivity (a boolean or low-cardinality enum column rarely justifies
a standalone index), a column that's write-heavy and rarely queried (index
maintenance cost outweighs read benefit), or a table small enough that a seq
scan is always fast regardless. Concretely here: `stores.sells_alcohol` is
filtered on every single search query but isn't indexed — it's low
cardinality and the store table is small (a few hundred rows across all
chains), so an index would add write overhead for no measurable read win.
That's a legitimate "no index needed" call, not an oversight.

**Q: Tell me about a real query performance problem you solved.**
A (use §4, compressed): "Our search endpoint combines free-text search with a
geo-radius filter. Both had supporting indexes — GIN trigram for text, GiST
for location — but the planner combined them into a plan that didn't use
either efficiently. I split the two predicates into materialized CTEs so each
independently produces a small, index-backed candidate ID set before the
outer query joins them, forcing the plan I wanted instead of hoping the
planner would find it. I verified with `EXPLAIN ANALYZE`, not by feel, and
left a comment flagging it as a targeted override that should be revisited if
the data shape or Postgres version changes."

**Q: How would this scale to 10x the data?**
A: See §12 below — B-tree/GiST/GIN all keep working at that scale, but I'd
watch (1) the materialized-CTE candidate sets growing large enough that
materializing them stops being cheap, (2) `price_history` outgrowing per-row
indexing in favor of BRIN + time-based partitioning, and (3) the
`store_ids_within_radius` cache TTL/bucketing needing to get smarter if
cardinality of distinct `(lat,lon,radius)` keys explodes.

**Q: What's a mistake you'd flag before being asked about it?**
A: The `MATERIALIZED` CTE override in `fetch_products` is exactly this kind
of thing — it's evidence-based today, but it's a hand override of the query
planner sitting in application code, and it has no automated regression test
that would catch a future Postgres upgrade silently making it unnecessary or
even counter-productive. It should have an `EXPLAIN`-based test or a periodic
manual `EXPLAIN ANALYZE` check, not just a comment.

---

## 12. System-design follow-up: what breaks first at 10x scale? **[General + Liquorfy]**

- **`prices` unique-constraint upserts** (`(product_id, store_id)`) stay cheap
  — B-tree unique lookups scale logarithmically. Not a concern until well
  past 10x.
- **Trigram GIN search** on `products.name`/`brand` degrades more than B-tree
  as the table grows, because GIN posting lists get longer and index size
  grows faster than data size for high-cardinality text. At real scale this
  is where you'd reach for a dedicated search engine (Postgres full-text
  `tsvector`, or an external engine like Elasticsearch/Meilisearch) instead
  of trigram-on-GIN — trigram is a great pragmatic choice for a catalog of
  tens of thousands of products, less so at tens of millions.
  Not a blocker to name today — right to name unprompted as a follow-up.
- **`price_history`** is append-only and will be the fastest-growing table by
  row count. At 10x, the honest fix is table partitioning by month on
  `recorded_at` (native Postgres declarative partitioning), which keeps each
  index small per partition and makes old partitions droppable/archivable
  instead of needing `DELETE` + `VACUUM`. BRIN on `recorded_at` per partition
  is also a strong fit given naturally time-ordered inserts.
  This is the strongest system-design answer in this section:
  *large, append-only, time-ordered table → partition it, don't just keep
  growing one B-tree.*
- **The materialized-CTE candidate sets** (§4) currently materialize small ID
  lists. If either predicate becomes far less selective at scale (e.g., a
  very common search term matching a huge fraction of products), the
  materialized set itself becomes large and the "force early reduction"
  trick stops paying for itself — would need re-validation with
  `EXPLAIN ANALYZE` against 10x data, exactly the kind of "revisit after data
  growth" caveat already flagged in the code comment.
- **Connection/session pressure**: more traffic means more concurrent
  connections; indexing doesn't fix that — pooling (PgBouncer/Supabase's
  pooler) and keeping transactions short does. Worth naming that indexing
  and connection management are separate levers, both needed.

---

## 13. Rapid-review cheat sheet

- B-tree: `=`, ranges, sort, prefix `LIKE`. Default choice.
- GIN: substring/fuzzy text (`pg_trgm`), JSONB containment, arrays. Slower writes.
- GiST: geometric/spatial (PostGIS), ranges, nearest-neighbor. Liquorfy's `stores.geog`.
- BRIN: huge, naturally-ordered tables (time-series). Not used here yet — right answer for `price_history` at scale.
- Composite index column order = leftmost-prefix rule. Put the equality/most-selective filter first, or match the range/sort pattern.
- Partial index when queries only touch a subset of rows — smaller, cheaper, sometimes doubles as a business-rule-enforcing unique constraint (`uq_ingestion_job_dedupe_key`).
- Index-only scan needs the index to cover every selected column *and* an up-to-date visibility map (`VACUUM`).
- `similarity()`/functions in `WHERE` don't automatically use an index unless the operator class supports it — check `LIKE`/`%` vs. plain function calls.
- CTEs inline by default since Postgres 12; `MATERIALIZED` forces the old optimization-fence behavior when you need to control the plan explicitly.
- Window functions (`ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)`) beat `GROUP BY` when you need "best row per group" + group aggregates without collapsing rows. Always give the `ORDER BY` a unique final tie-breaker.
- `CREATE INDEX CONCURRENTLY` avoids blocking writes on a live table; can't run inside a transaction; can fail and leave an `INVALID` index.
- Every index costs write throughput, storage, and vacuum time — index for real queries, not speculatively.
- Caching (Redis) complements indexing, doesn't replace it — cache the hot, low-cardinality-key path; let the indexed query carry the long tail; never make correctness depend on the cache being up.
- Always verify with `EXPLAIN (ANALYZE, BUFFERS)` against realistic data volume — planner behavior on a near-empty dev DB is not representative.
