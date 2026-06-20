"""
Countdown / Woolworths NZ API scraper — PER-STORE pricing.

Woolworths NZ prices and availability vary by store. The products search API
(`/api/v1/products`) returns results scoped to the session's selected fulfilment
store. We therefore iterate every store: set the store, then scrape its catalogue.

Setting the store (reverse-engineered from the site's Angular bundle —
`changeSelectedPickupStore = id => apiService.put(postStoreEndpoint, {addressId:id})`):
    PUT /api/v1/fulfilment/my/pickup-addresses   body {"addressId": <id>}
The `addressId` is stored per store as `Store.api_id` (backfilled from
`/api/v1/addresses/pickup-addresses`). Products a store doesn't stock come back
with a sentinel price of 0 / 99999.99 — those are skipped.

Note: Countdown NZ rebranded to Woolworths NZ (October 2023); the live site and
API are at woolworths.co.nz.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import quote

import httpx
from sqlalchemy import select

from app.db.models import IngestionRun, Store
from app.db.session import async_transaction, get_async_session
from app.scrapers.base import Scraper
from app.services.parser_utils import infer_brand

logger = logging.getLogger(__name__)

PERSIST_BATCH_SIZE = 200


class CountdownAPIScraper(Scraper):
    """Per-store API scraper for Woolworths NZ (formerly Countdown)."""

    chain = "countdown"
    _sweep_per_store = True

    site_url = "https://www.woolworths.co.nz"
    api_url = "https://www.woolworths.co.nz/api/v1/products"
    # Endpoint that sets the session's fulfilment store (controls pricing/availability)
    set_store_url = "https://www.woolworths.co.nz/api/v1/fulfilment/my/pickup-addresses"

    # Number of stores scraped concurrently (each in its own session/cookie jar).
    # The fulfilment store is session-global, so stores cannot share a session.
    STORE_CONCURRENCY = 4
    # Delay between paginated requests within a store (politeness)
    PAGE_DELAY = 0.3

    # Search terms for beer, cider, and wine (NZ supermarkets cannot sell spirits).
    search_terms = [
        "beer", "lager", "ale", "cider",
        "sauvignon blanc", "pinot noir", "merlot", "chardonnay",
        "pinot gris", "rose wine", "sparkling wine", "champagne",
    ]

    _ALCOHOL_DEPT = "Beer & Wine"

    _USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )

    def __init__(self, scrape_all_stores: bool = True):
        Scraper.__init__(self)
        self.scrape_all_stores = scrape_all_stores

    # ------------------------------------------------------------------
    # Store handling
    # ------------------------------------------------------------------

    def _api_headers(self) -> dict:
        return {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-NZ",
            "content-type": "application/json",
            "user-agent": self._USER_AGENT,
            "x-requested-with": "OnlineShopping.WebApp",
            "cache-control": "no-cache",
        }

    async def _load_stores(self) -> List[dict]:
        """Load countdown stores that have a fulfilment addressId (api_id)."""
        stores: List[dict] = []
        async with get_async_session() as session:
            result = await session.execute(
                select(Store.api_id, Store.name)
                .where(Store.chain == self.chain)
                .where(Store.api_id.is_not(None))
            )
            for api_id, name in result.all():
                if api_id:
                    stores.append({"id": str(api_id), "name": name or str(api_id)})
        # Pilot/limit support: LIQUORFY_COUNTDOWN_STORE_LIMIT caps the number of
        # stores scraped (e.g. for a staged rollout). Unset = all stores.
        limit = os.environ.get("LIQUORFY_COUNTDOWN_STORE_LIMIT")
        if limit:
            try:
                n = int(limit)
                if n > 0 and n < len(stores):
                    logger.info(f"countdown: store limit active — scraping {n}/{len(stores)} stores")
                    stores = stores[:n]
            except ValueError:
                pass
        return stores

    async def _new_session(self) -> httpx.AsyncClient:
        """Create a client with a fresh Woolworths session (own cookie jar)."""
        client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        try:
            await client.get(self.site_url, headers={"user-agent": self._USER_AGENT})
        except Exception as e:
            logger.debug(f"countdown: session warmup failed: {e}")
        return client

    async def _set_store(self, client: httpx.AsyncClient, address_id: str) -> bool:
        """Set the session's fulfilment store so products are priced for it."""
        try:
            resp = await client.put(
                self.set_store_url,
                headers=self._api_headers(),
                json={"addressId": int(address_id)},
            )
            return resp.status_code < 400
        except Exception as e:
            logger.warning(f"countdown: failed to set store {address_id}: {e}")
            return False

    async def _fetch_search(
        self,
        client: httpx.AsyncClient,
        term: str,
        page: int = 1,
        size: int = 120,
    ) -> dict:
        """Fetch one page of search results for the session's current store."""
        headers = dict(self._api_headers())
        headers["referer"] = f"{self.site_url}/shop/search?search={quote(term)}"
        url = (
            f"{self.api_url}?target=search&search={quote(term)}"
            f"&page={page}&size={size}&inStockProductsOnly=false"
        )
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse_product(self, product_data: dict) -> dict:
        """Parse a product from the API response into our standard format."""
        sku = product_data.get("sku") or ""
        name = product_data.get("name") or ""
        brand = product_data.get("brand") or ""
        variety = product_data.get("variety") or ""

        # The Woolworths API's `name` field already contains the brand and
        # variety prefix (e.g. "Kim Crawford Chardonnay 750mL"), so use it
        # verbatim. Concatenating brand + variety + name tripled the prefix.
        full_name = name.strip()
        if not full_name:
            full_name = " ".join(p for p in (brand, variety) if p).strip()

        price_info = product_data.get("price", {}) or {}
        price = price_info.get("originalPrice", 0)
        sale_price = price_info.get("salePrice")
        is_special = price_info.get("isSpecial", False)

        promo_price = None
        promo_text = None
        if is_special and sale_price and sale_price < price:
            promo_price = sale_price
            save_price = price_info.get("savePrice", 0)
            if save_price:
                promo_text = f"Save ${save_price:.2f}"[:255]

        is_member_only = price_info.get("isClubPrice", False)

        images = product_data.get("images", {})
        image_url = images.get("big") or images.get("small")

        slug = product_data.get("slug", "")
        url = (
            f"https://www.woolworths.co.nz/shop/productdetails?stockcode={sku}&name={slug}"
            if slug else None
        )

        size_info = product_data.get("size", {})
        volume_size = size_info.get("volumeSize", "")  # e.g. "24 x 330mL"
        if volume_size:
            full_name = f"{full_name} {volume_size}"

        inferred_brand = infer_brand(full_name)

        return self.build_product_dict(
            source_id=sku,
            name=full_name,
            price_nzd=price,
            promo_price_nzd=promo_price,
            promo_text=promo_text,
            promo_ends_at=None,
            is_member_only=is_member_only,
            url=url,
            image_url=image_url,
            brand=inferred_brand or brand,
        )

    @staticmethod
    def _is_stocked(product_data: dict) -> bool:
        """Products a store doesn't carry come back priced 0 (or a 99999.99 sentinel)."""
        price_info = product_data.get("price", {}) or {}
        original = price_info.get("originalPrice") or 0
        sale = price_info.get("salePrice") or 0
        effective = sale or original
        return bool(effective) and 0 < effective < 90000

    async def fetch_catalog_pages(self) -> List[str]:
        """Not used for API-based scraper."""
        return []

    async def parse_products(self, payload: str) -> List[dict]:
        """Not used for API-based scraper."""
        return []

    # ------------------------------------------------------------------
    # Per-store scrape
    # ------------------------------------------------------------------

    async def _scrape_store(self, address_id: str, store_name: str) -> List[dict]:
        """Set the store, then scrape its priced alcohol catalogue."""
        products: List[dict] = []
        seen_skus: set[str] = set()

        client = await self._new_session()
        try:
            if not await self._set_store(client, address_id):
                logger.warning(f"countdown: could not select store {store_name} ({address_id})")
                return []

            for term in self.search_terms:
                page_num = 1
                while True:
                    try:
                        response = await self._fetch_search(client, term, page=page_num)
                    except Exception as e:
                        logger.debug(f"countdown {store_name}: '{term}' p{page_num} failed: {e}")
                        break

                    items = response.get("products", {}).get("items", []) or []
                    if not items:
                        break

                    for item_data in items:
                        depts = item_data.get("departments") or []
                        if not any(d.get("name") == self._ALCOHOL_DEPT for d in depts):
                            continue
                        sku = str(item_data.get("sku") or "")
                        if not sku or sku in seen_skus:
                            continue
                        if not self._is_stocked(item_data):
                            continue  # not carried by this store
                        seen_skus.add(sku)
                        product = self._parse_product(item_data)
                        if product.get("price_nzd") and product["price_nzd"] > 0:
                            products.append(product)

                    if len(items) < 120:
                        break
                    page_num += 1
                    await asyncio.sleep(self.PAGE_DELAY)
        finally:
            await client.aclose()

        logger.info(f"countdown {store_name}: {len(products)} priced products")
        return products

    async def scrape(self) -> List[dict]:
        """Compatibility helper: scrape the default (first) store only."""
        stores = await self._load_stores()
        if not stores:
            return []
        return await self._scrape_store(stores[0]["id"], stores[0]["name"])

    # ------------------------------------------------------------------
    # Run (per-store persistence)
    # ------------------------------------------------------------------

    async def run(self) -> IngestionRun:
        """Scrape every store and persist prices per store."""
        self._run_started_at = datetime.now(timezone.utc)

        run = IngestionRun(chain=self.chain, status="running", started_at=self._run_started_at)
        async with async_transaction() as session:
            session.add(run)
            await session.flush()

        try:
            stores = await self._load_stores()
            if not stores:
                raise RuntimeError("No countdown stores with api_id (run store backfill first)")
            logger.info(f"countdown: scraping {len(stores)} stores (concurrency={self.STORE_CONCURRENCY})")

            # Resolve api_id -> Store once
            api_ids = [s["id"] for s in stores]
            store_map: dict[str, Store] = {}
            async with async_transaction() as session:
                result = await session.execute(
                    select(Store).where(
                        Store.chain == self.chain, Store.api_id.in_(api_ids)
                    )
                )
                for st in result.scalars().all():
                    store_map[st.api_id] = st

            totals = {"items": 0, "changed": 0, "failed": 0}
            seen_store_ids: set = set()
            sem = asyncio.Semaphore(self.STORE_CONCURRENCY)

            async def handle(store: dict) -> None:
                api_id = str(store["id"])
                db_store = store_map.get(api_id)
                if not db_store:
                    return
                async with sem:
                    try:
                        products = await self._scrape_store(api_id, store["name"])
                    except Exception as e:
                        logger.error(f"countdown: store {store['name']} scrape failed: {e}")
                        return
                if not products:
                    return
                totals["items"] += len(products)
                seen_store_ids.add(db_store.id)
                for batch_start in range(0, len(products), PERSIST_BATCH_SIZE):
                    batch = products[batch_start:batch_start + PERSIST_BATCH_SIZE]
                    try:
                        async with async_transaction() as session:
                            changed = await self._upsert_products_batch(session, batch, [db_store])
                        totals["changed"] += changed
                    except Exception as e:
                        logger.error(f"countdown: persist batch for {store['name']} failed: {e}")
                        totals["failed"] += len(batch)

            await asyncio.gather(*(handle(s) for s in stores))

            # Per-store stale-promo sweep
            if self._run_started_at and seen_store_ids:
                try:
                    from app.services.freshness import sweep_store_promos
                    async with async_transaction() as session:
                        for sid in seen_store_ids:
                            await sweep_store_promos(session, sid, self._run_started_at)
                except Exception as e:
                    logger.warning(f"countdown: per-store promo sweep failed: {e}")

            status = "completed" if totals["items"] > 0 else "failed"
            error_msg = None if totals["items"] > 0 else "No products scraped (likely auth/store-set failure)"
            async with async_transaction() as session:
                result = await session.execute(select(IngestionRun).where(IngestionRun.id == run.id))
                run = result.scalar_one()
                run.status = status
                run.finished_at = datetime.now(timezone.utc)
                run.items_total = totals["items"]
                run.items_changed = totals["changed"]
                run.items_failed = totals["failed"]
                run.error_message = error_msg

            logger.info(
                f"countdown completed: {totals['items']} items across {len(seen_store_ids)} stores, "
                f"{totals['changed']} changed, {totals['failed']} failed"
            )
            return run

        except asyncio.CancelledError:
            logger.error(f"Scraper cancelled: {self.chain}")
            async with async_transaction() as session:
                result = await session.execute(select(IngestionRun).where(IngestionRun.id == run.id))
                run = result.scalar_one()
                run.status = "failed"
                run.finished_at = datetime.now(timezone.utc)
                run.error_message = "Cancelled (timeout)"
            raise

        except Exception as e:
            logger.error(f"Scraper failed: {e}")
            async with async_transaction() as session:
                result = await session.execute(select(IngestionRun).where(IngestionRun.id == run.id))
                run = result.scalar_one()
                run.status = "failed"
                run.finished_at = datetime.now(timezone.utc)
                run.error_message = f"{type(e).__name__}: {e}"[:1000]
            raise


__all__ = ["CountdownAPIScraper"]
