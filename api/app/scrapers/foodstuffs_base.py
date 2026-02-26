"""
Base scraper for Foodstuffs chains (New World, PakNSave) using their shared API infrastructure.
Both chains use identical API endpoints with only different domains and store IDs.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import httpx
from sqlalchemy import select

from app.db.models import IngestionRun, Store
from app.db.session import async_transaction, get_async_session
from app.scrapers.base import Scraper
from app.scrapers.api_auth_base import APIAuthBase
from app.services.parser_utils import infer_brand

logger = logging.getLogger(__name__)


class FoodstuffsAPIScraper(Scraper, APIAuthBase):
    """
    Base scraper for Foodstuffs chains (New World, PakNSave).

    Both chains share the same API infrastructure with only different domains.
    Subclasses must define: chain, site_url, api_domain, api_url, default_store_id, store_data_file
    """

    # Subclasses must override these
    chain: str = None
    site_url: str = None
    api_domain: str = None
    api_url: str = None
    default_store_id: str = None
    store_data_file: str = None  # e.g., "newworld_stores.json"

    # Shared category definitions for both chains
    categories = [
        ("Beer, Wine & Cider", "Beer"),
        ("Beer, Wine & Cider", "Craft Beer"),
        ("Beer, Wine & Cider", "Cider"),
        ("Beer, Wine & Cider", "Red Wine"),
        ("Beer, Wine & Cider", "White Wine"),
        ("Beer, Wine & Cider", "Rosé Wine"),
        ("Beer, Wine & Cider", "Champagne & Sparkling Wine"),
        ("Beer, Wine & Cider", "Seltzers & Other Alcoholic Drinks"),
    ]

    def __init__(self, scrape_all_stores: bool = True):
        Scraper.__init__(self)
        APIAuthBase.__init__(self)
        self.store_id: str = self.default_store_id
        self.scrape_all_stores = scrape_all_stores
        self.store_list = self._load_store_list() if scrape_all_stores else []

    async def _load_store_list_from_db(self) -> List[dict]:
        """Load store API IDs for this chain from database (source of truth)."""
        stores: List[dict] = []

        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(Store.api_id, Store.name)
                    .where(Store.chain == self.chain)
                    .where(Store.api_id.is_not(None))
                )
                for api_id, name in result.all():
                    if not api_id:
                        continue
                    stores.append({"id": str(api_id), "name": name or str(api_id)})

        except Exception as e:
            logger.warning(f"Failed loading {self.chain} stores from DB, using fallback list: {e}")
            return []

        return stores

    def _load_store_list(self) -> List[dict]:
        """Load store list from JSON file."""
        try:
            current_dir = Path(__file__).parent
            data_file = current_dir.parent / "data" / self.store_data_file

            if not data_file.exists():
                logger.warning(f"Store list file not found: {data_file}")
                return []

            with open(data_file, 'r') as f:
                stores = json.load(f)

            logger.info(f"Loaded {len(stores)} {self.chain} stores from {data_file}")
            return stores
        except Exception as e:
            logger.error(f"Failed to load store list: {e}")
            return []

    async def _get_auth_token(self) -> Optional[str]:
        """Get authentication token.

        Strategy (in order):
        1. Direct HTTP call to /api/user/get-current-user (fast, no browser).
        2. Browser-based capture (fallback for if the direct endpoint changes).
        """
        # --- Fast path: direct HTTP token request ---
        token = await self._get_token_direct()
        if token:
            return token

        logger.warning(f"{self.chain}: direct token request failed, falling back to browser auth")

        # --- Slow path: browser-based capture ---
        return await self._get_auth_via_browser(
            capture_token=True,
            capture_cookies=True,
            headless=True,
            wait_time=10.0
        )

    async def _get_token_direct(self) -> Optional[str]:
        """Request a guest auth token directly via the site's Next.js API route.

        Calls POST /api/user/get-current-user which returns
        {"access_token": "<jwt>", ...} and sets session cookies.
        This avoids needing a browser or dealing with Cloudflare challenges.
        """
        domain = self.site_url.split("//")[-1].split("/")[0]
        url = f"https://{domain}/api/user/get-current-user"

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "origin": f"https://{domain}",
            "referer": f"https://{domain}/",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.post(url, headers=headers, json={})
                resp.raise_for_status()
                data = resp.json()

                token = data.get("access_token")
                if not token:
                    logger.warning(f"{self.chain}: /api/user/get-current-user returned no access_token")
                    return None

                # Capture cookies from the response (fs-user-token, refresh_token, etc.)
                self.cookies = {name: value for name, value in resp.cookies.items()}
                logger.info(
                    f"{self.chain}: obtained auth token via direct HTTP "
                    f"({len(token)} chars, {len(self.cookies)} cookies)"
                )
                return token

        except Exception as e:
            logger.warning(f"{self.chain}: direct token request failed: {e}")
            return None

    async def _fetch_category(
        self,
        level0: str,
        level1: str,
        page: int = 0,
        hits_per_page: int = 100
    ) -> dict:
        """
        Fetch products for a specific category using the API.

        Args:
            level0: Top-level category (e.g., "Beer, Wine & Cider")
            level1: Sub-category (e.g., "Beer")
            page: Page number (0-indexed)
            hits_per_page: Number of products per page

        Returns:
            API response dict with products
        """
        # Parse domain for origin/referer headers
        domain = self.site_url.split("//")[-1].split("/")[0]

        headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "origin": f"https://{domain}",
            "referer": f"https://{domain}/",
        }
        if self.auth_token:
            headers["authorization"] = f"Bearer {self.auth_token}"

        # Add cookies if we have them
        if self.cookies:
            cookie_string = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
            headers["cookie"] = cookie_string

        payload = {
            "algoliaQuery": {
                "attributesToHighlight": [],
                "attributesToRetrieve": [
                    "productID",
                    "Type",
                    "sponsored",
                    "category0NI",
                    "category1NI",
                    "category2NI"
                ],
                "facets": [
                    "brand",
                    "category2NI",
                    "onPromotion",
                    "productFacets",
                    "tobacco"
                ],
                "filters": f'stores:{self.store_id} AND category0NI:"{level0}" AND category1NI:"{level1}"',
                "hitsPerPage": hits_per_page,
                "page": page,
            },
            "storeId": self.store_id,
            "hitsPerPage": hits_per_page,
            "page": page,
            "sortOrder": "NI_POPULARITY_ASC",
            "tobaccoQuery": False,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def _probe_cookie_only_access(self) -> bool:
        """Check whether API access works without bearer token using session cookies only."""
        if not self.categories:
            return False

        level0, level1 = self.categories[0]
        try:
            await self._fetch_category(level0, level1, page=0, hits_per_page=1)
            return True
        except Exception as e:
            logger.warning(f"Cookie-only API probe failed for {self.chain}: {e}")
            return False

    def _parse_product(self, product_data: dict) -> dict:
        """
        Parse a product from API response into our standard format.

        Args:
            product_data: Product dict from API

        Returns:
            Standardized product dict
        """
        # Extract basic info
        product_id = product_data.get("productId", "")
        brand = product_data.get("brand", "")
        name = product_data.get("name", "")
        display_name = product_data.get("displayName", "")

        # Full product name
        full_name = f"{brand} {name} {display_name}".strip()

        # Price (in cents, convert to dollars)
        price_cents = product_data.get("singlePrice", {}).get("price", 0)
        price = price_cents / 100

        # Promotions
        promo_price = None
        promo_text = None
        promo_ends_at = None
        is_member_only = False

        promotions = product_data.get("promotions", [])
        if promotions:
            # Get the best promotion (they mark it)
            best_promo = next(
                (p for p in promotions if p.get("bestPromotion")),
                promotions[0] if promotions else None
            )

            if best_promo:
                reward_value = best_promo.get("rewardValue")
                if reward_value and reward_value < price_cents:
                    promo_price = reward_value / 100

                # Build promo text
                reward_type = best_promo.get("rewardType", "")
                decal = best_promo.get("decal", "")
                if decal:
                    promo_text = decal[:255]
                elif reward_type == "NEW_PRICE":
                    promo_text = "Special Price"

                # Check for member-only (cardDependencyFlag)
                is_member_only = best_promo.get("cardDependencyFlag", False)

        # Image URL (construct from product ID)
        product_id_prefix = product_id.split("-")[0] if "-" in product_id else product_id
        image_url = f"https://a.fsimg.co.nz/product/retail/fan/image/400x400/{product_id_prefix}.png"

        # Product URL - extract domain from site_url
        domain = self.site_url.split("//")[-1].split("/")[0]
        slug = full_name.lower().replace(" ", "-").replace("'", "")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        url = f"https://{domain}/shop/product/{product_id.lower().replace('-', '_')}?name={slug}"

        # Use standardized product dict builder
        inferred_brand = infer_brand(full_name)

        return self.build_product_dict(
            source_id=product_id,
            name=full_name,
            price_nzd=price,
            promo_price_nzd=promo_price,
            promo_text=promo_text,
            promo_ends_at=promo_ends_at,
            is_member_only=is_member_only,
            url=url,
            image_url=image_url,
            brand=inferred_brand or brand,
        )

    async def fetch_catalog_pages(self) -> List[str]:
        """Not used for API-based scraper - implemented for base class compatibility."""
        return []

    async def parse_products(self, payload: str) -> List[dict]:
        """Not used for API-based scraper - implemented for base class compatibility."""
        return []

    _sweep_per_store = True

    async def run(self) -> IngestionRun:
        """
        Run the scraper and persist data to database.
        Overrides base class to use API-based scraping instead of HTML parsing.
        """
        self._run_started_at = datetime.utcnow()

        run = IngestionRun(
            chain=self.chain,
            status="running",
            started_at=self._run_started_at,
        )

        async with async_transaction() as session:
            session.add(run)
            await session.flush()

        try:
            products = await self.scrape()
            total_items = len(products)
            changed_items = 0
            failed_items = 0

            # Track store UUIDs we actually wrote to, for per-store sweep
            seen_store_ids: set = set()

            # Process each product in its own transaction to avoid cascade failures
            for product_data in products:
                try:
                    async with async_transaction() as session:
                        store_api_id = product_data.get('store_id')
                        if store_api_id:
                            result = await session.execute(
                                select(Store).where(
                                    Store.chain == self.chain,
                                    Store.api_id == store_api_id
                                )
                            )
                            store = result.scalar_one_or_none()

                            if store:
                                seen_store_ids.add(store.id)
                                changed = await self._upsert_product_and_prices(
                                    session, product_data, [store]
                                )
                                if changed:
                                    changed_items += 1
                            else:
                                logger.debug(f"Store not found in DB for api_id={store_api_id}, skipping price")
                                failed_items += 1
                        else:
                            logger.warning(f"Product {product_data.get('name')} has no store_id")
                            failed_items += 1
                except Exception as e:
                    logger.error(f"Failed to persist product {product_data.get('name')}: {e}")
                    failed_items += 1

            # Sweep stale promos for each store we scraped
            if self._run_started_at and seen_store_ids:
                try:
                    from app.services.freshness import sweep_store_promos

                    async with async_transaction() as session:
                        for sid in seen_store_ids:
                            await sweep_store_promos(session, sid, self._run_started_at)
                except Exception as e:
                    logger.warning(f"Per-store promo sweep failed for chain={self.chain}: {e}")

            # Mark as failed if auth produced zero items (likely auth failure)
            status = "failed" if total_items == 0 else "completed"

            async with async_transaction() as session:
                result = await session.execute(
                    select(IngestionRun).where(IngestionRun.id == run.id)
                )
                run = result.scalar_one()
                run.status = status
                run.finished_at = datetime.utcnow()
                run.items_total = total_items
                run.items_changed = changed_items
                run.items_failed = failed_items

            logger.info(
                f"Scraper completed: {total_items} items, "
                f"{changed_items} changed, {failed_items} failed"
            )
            return run

        except Exception as e:
            logger.error(f"Scraper failed: {e}")
            async with async_transaction() as session:
                result = await session.execute(
                    select(IngestionRun).where(IngestionRun.id == run.id)
                )
                run = result.scalar_one()
                run.status = "failed"
                run.finished_at = datetime.utcnow()
            raise

    async def _validate_auth(self) -> bool:
        """Validate that the auth token is still valid by making a lightweight API call."""
        if not self.categories:
            return False
        level0, level1 = self.categories[0]
        try:
            response = await self._fetch_category(level0, level1, page=0, hits_per_page=1)
            count = response.get("totalProducts", 0)
            logger.info(f"{self.chain}: auth validation passed ({count} products in {level1})")
            return True
        except Exception as e:
            logger.warning(f"{self.chain}: auth validation failed: {e}")
            return False

    async def scrape(self) -> List[dict]:
        """
        Scrape all products using the Foodstuffs API.

        Returns:
            List of product dictionaries
        """
        if not self.auth_token:
            self.auth_token = await self._get_auth_token()
            if not self.auth_token:
                logger.error(
                    f"Unable to authenticate {self.chain}: "
                    "both direct HTTP and browser token capture failed"
                )
                return []

        # Validate auth before full scrape
        if not await self._validate_auth():
            logger.warning(f"{self.chain}: stale token detected, refreshing...")
            self.auth_token = await self._get_auth_token()
            if not self.auth_token or not await self._validate_auth():
                logger.error(f"{self.chain}: auth validation failed after refresh")
                return []

        all_products: List[dict] = []

        # Determine which stores to scrape
        stores_to_scrape = []
        if self.scrape_all_stores:
            db_stores = await self._load_store_list_from_db()
            if db_stores:
                stores_to_scrape = db_stores
                logger.info(f"Scraping all {len(stores_to_scrape)} {self.chain} stores from database")
            elif self.store_list:
                stores_to_scrape = self.store_list
                logger.info(f"Scraping all {len(stores_to_scrape)} {self.chain} stores from JSON fallback")
            else:
                stores_to_scrape = [{"id": self.default_store_id, "name": "Default Store"}]
                logger.warning(f"No {self.chain} store list found in DB/JSON; scraping default store only")
        else:
            stores_to_scrape = [{"id": self.default_store_id, "name": "Default Store"}]
            logger.info("Scraping single store (default)")

        # Scrape each store
        for store_idx, store in enumerate(stores_to_scrape, 1):
            store_id = store["id"]
            store_name = store.get("name", store_id)

            logger.info(f"[{store_idx}/{len(stores_to_scrape)}] Scraping store: {store_name}")
            self.store_id = store_id

            # Scrape each category for this store
            for level0, level1 in self.categories:
                logger.info(f"  Category: {level0} > {level1}")

                try:
                    response = await self._fetch_category(level0, level1, page=0)
                    products_data = response.get("products", [])
                    total_products = response.get("totalProducts", len(products_data))

                    logger.info(f"  Found {total_products} products in {level1}")

                    # Parse products from first page
                    for product_data in products_data:
                        try:
                            product = self._parse_product(product_data)
                            product["store_id"] = store_id
                            product["store_name"] = store_name
                            all_products.append(product)
                        except Exception as e:
                            logger.error(f"Error parsing product: {e}")

                    # Fetch remaining pages if needed
                    hits_per_page = 100
                    total_pages = (total_products + hits_per_page - 1) // hits_per_page

                    for page_num in range(1, total_pages):
                        logger.info(f"  Fetching page {page_num + 1}/{total_pages} for {level1}")

                        response = await self._fetch_category(level0, level1, page=page_num)
                        products_data = response.get("products", [])

                        for product_data in products_data:
                            try:
                                product = self._parse_product(product_data)
                                product["store_id"] = store_id
                                product["store_name"] = store_name
                                all_products.append(product)
                            except Exception as e:
                                logger.error(f"Error parsing product: {e}")

                        await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"Error scraping category {level1}: {e}")
                    continue

                await asyncio.sleep(0.3)

            # Delay between stores to avoid rate limiting
            if store_idx < len(stores_to_scrape):
                await asyncio.sleep(2)

        logger.info(f"Successfully scraped {len(all_products)} products from {self.chain} ({len(stores_to_scrape)} stores)")
        return all_products


__all__ = ["FoodstuffsAPIScraper"]
