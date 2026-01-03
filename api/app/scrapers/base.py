from __future__ import annotations

import abc
import logging
from datetime import datetime
from typing import Iterable, List, Optional
from uuid import UUID

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.config import get_settings
from app.db.models import IngestionRun, Price, Product, Store
from app.db.session import async_transaction


settings = get_settings()
logger = logging.getLogger(__name__)


class Scraper(abc.ABC):
    chain: str
    catalog_urls: List[str] = []  # Override in subclasses for HTTP mode

    def __init__(self, use_fixtures: bool = True) -> None:
        self.client = AsyncClient(timeout=20)
        self.use_fixtures = use_fixtures

    async def run(self) -> IngestionRun:
        """Run the scraper and persist data to database."""
        # Create ingestion run record
        run = IngestionRun(
            chain=self.chain,
            status="running",
            started_at=datetime.utcnow(),
        )

        async with async_transaction() as session:
            session.add(run)
            await session.flush()

        try:
            # Fetch and process catalog pages
            pages = await self.fetch_catalog_pages()
            total_items = 0
            changed_items = 0
            failed_items = 0

            async with async_transaction() as session:
                # Get all stores for this chain
                result = await session.execute(
                    select(Store).where(Store.chain == self.chain)
                )
                stores = result.scalars().all()

                if not stores:
                    logger.warning(f"No stores found for chain {self.chain}")
                    stores = []

                for page in pages:
                    try:
                        products = await self.parse_products(page)
                        total_items += len(products)

                        # Batch process products for better performance
                        changed_count = await self._upsert_products_batch(
                            session, products, stores
                        )
                        changed_items += changed_count
                        failed_items += len(products) - changed_count

                    except Exception as e:
                        logger.error(f"Failed to parse page: {e}")
                        failed_items += 1

            # Update ingestion run with results
            async with async_transaction() as session:
                result = await session.execute(
                    select(IngestionRun).where(IngestionRun.id == run.id)
                )
                run = result.scalar_one()
                run.status = "completed"
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
            # Update run status to failed
            async with async_transaction() as session:
                result = await session.execute(
                    select(IngestionRun).where(IngestionRun.id == run.id)
                )
                run = result.scalar_one()
                run.status = "failed"
                run.finished_at = datetime.utcnow()
            raise

    def build_product_dict(
        self,
        *,
        source_id: str,
        name: str,
        price_nzd: float,
        promo_price_nzd: Optional[float] = None,
        promo_text: Optional[str] = None,
        promo_ends_at: Optional[datetime] = None,
        is_member_only: bool = False,
        url: Optional[str] = None,
        image_url: Optional[str] = None,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        **kwargs  # Allow additional fields
    ) -> dict:
        """
        Build standardized product dictionary with auto-parsing.

        Automatically infers brand, category, volume, and ABV from name
        if not explicitly provided.

        Args:
            source_id: Product ID from source website
            name: Full product name
            price_nzd: Regular price in NZD
            promo_price_nzd: Promotional price (optional)
            promo_text: Promotional text (optional)
            promo_ends_at: Promo end date (optional)
            is_member_only: Member-only pricing flag
            url: Product URL
            image_url: Product image URL
            brand: Brand name (auto-inferred if None)
            category: Category (auto-inferred if None)
            **kwargs: Additional fields to include

        Returns:
            Standardized product dictionary
        """
        from app.services.parser_utils import (
            parse_volume, extract_abv, infer_brand, infer_category
        )

        # Parse volume from name
        volume = parse_volume(name)

        return {
            "chain": self.chain,
            "source_id": source_id,
            "name": name,
            "brand": brand or infer_brand(name),
            "category": category or infer_category(name),
            "price_nzd": price_nzd,
            "promo_price_nzd": promo_price_nzd,
            "promo_text": promo_text[:255] if promo_text else None,
            "promo_ends_at": promo_ends_at,
            "is_member_only": is_member_only,
            "pack_count": volume.pack_count,
            "unit_volume_ml": volume.unit_volume_ml,
            "total_volume_ml": volume.total_volume_ml,
            "abv_percent": extract_abv(name),
            "url": url,
            "image_url": image_url,
            **kwargs  # Additional fields
        }

    async def _upsert_products_batch(
        self, session, products_data: List[dict], stores: List[Store]
    ) -> int:
        """
        Batch upsert products and their prices for better performance.
        Returns count of changed items.
        """
        if not products_data:
            return 0

        now = datetime.utcnow()
        changed_count = 0

        # Step 1: Bulk upsert all products
        product_values = []
        for product_data in products_data:
            product_values.append({
                "chain": product_data["chain"],
                "source_product_id": product_data["source_id"],
                "name": product_data["name"],
                "brand": product_data.get("brand"),
                "category": product_data.get("category"),
                "abv_percent": product_data.get("abv_percent"),
                "pack_count": product_data.get("pack_count"),
                "unit_volume_ml": product_data.get("unit_volume_ml"),
                "total_volume_ml": product_data.get("total_volume_ml"),
                "image_url": product_data.get("image_url"),
                "product_url": product_data.get("url"),
            })

        stmt = insert(Product).values(product_values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["chain", "source_product_id"],
            set_={
                "name": stmt.excluded.name,
                "brand": stmt.excluded.brand,
                "category": stmt.excluded.category,
                "abv_percent": stmt.excluded.abv_percent,
                "pack_count": stmt.excluded.pack_count,
                "unit_volume_ml": stmt.excluded.unit_volume_ml,
                "total_volume_ml": stmt.excluded.total_volume_ml,
                "image_url": stmt.excluded.image_url,
                "product_url": stmt.excluded.product_url,
                "updated_at": now,
            },
        )
        await session.execute(stmt)
        await session.flush()

        # Step 2: Get product IDs for all upserted products
        source_ids = [p["source_id"] for p in products_data]
        result = await session.execute(
            select(Product.id, Product.source_product_id).where(
                Product.chain == self.chain,
                Product.source_product_id.in_(source_ids)
            )
        )
        product_id_map = {row.source_product_id: row.id for row in result}

        # Step 3: Get all existing prices in one query
        product_ids = list(product_id_map.values())
        store_ids = [store.id for store in stores]

        existing_prices_result = await session.execute(
            select(Price).where(
                Price.product_id.in_(product_ids),
                Price.store_id.in_(store_ids)
            )
        )
        existing_prices = existing_prices_result.scalars().all()

        # Create lookup map: (product_id, store_id) -> Price
        existing_prices_map = {
            (price.product_id, price.store_id): price
            for price in existing_prices
        }

        # Step 4: Bulk upsert prices
        price_values = []
        for product_data in products_data:
            product_id = product_id_map.get(product_data["source_id"])
            if not product_id:
                continue

            for store in stores:
                existing_price = existing_prices_map.get((product_id, store.id))

                # Check if price changed
                price_changed = False
                if existing_price:
                    if (
                        existing_price.price_nzd != product_data["price_nzd"]
                        or existing_price.promo_price_nzd != product_data.get("promo_price_nzd")
                        or existing_price.is_member_only != product_data.get("is_member_only", False)
                    ):
                        price_changed = True
                        changed_count += 1

                # Always include in bulk upsert (will update last_seen_at)
                price_values.append({
                    "product_id": product_id,
                    "store_id": store.id,
                    "price_nzd": product_data["price_nzd"],
                    "promo_price_nzd": product_data.get("promo_price_nzd"),
                    "promo_text": product_data.get("promo_text"),
                    "promo_ends_at": product_data.get("promo_ends_at"),
                    "is_member_only": product_data.get("is_member_only", False),
                    "last_seen_at": now,
                    "price_last_changed_at": now if (price_changed or not existing_price) else (existing_price.price_last_changed_at if existing_price else now),
                })

                if not existing_price:
                    changed_count += 1

        # Bulk insert with ON CONFLICT
        if price_values:
            stmt = insert(Price).values(price_values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["product_id", "store_id"],
                set_={
                    "price_nzd": stmt.excluded.price_nzd,
                    "promo_price_nzd": stmt.excluded.promo_price_nzd,
                    "promo_text": stmt.excluded.promo_text,
                    "promo_ends_at": stmt.excluded.promo_ends_at,
                    "is_member_only": stmt.excluded.is_member_only,
                    "last_seen_at": stmt.excluded.last_seen_at,
                    "price_last_changed_at": stmt.excluded.price_last_changed_at,
                },
            )
            await session.execute(stmt)

        return changed_count

    async def _upsert_product_and_prices(
        self, session, product_data: dict, stores: List[Store]
    ) -> bool:
        """
        Upsert product and its prices.
        Returns True if any changes were made, False otherwise.
        """
        now = datetime.utcnow()
        changed = False

        # Upsert product
        stmt = insert(Product).values(
            chain=product_data["chain"],
            source_product_id=product_data["source_id"],
            name=product_data["name"],
            brand=product_data.get("brand"),
            category=product_data.get("category"),
            abv_percent=product_data.get("abv_percent"),
            pack_count=product_data.get("pack_count"),
            unit_volume_ml=product_data.get("unit_volume_ml"),
            total_volume_ml=product_data.get("total_volume_ml"),
            image_url=product_data.get("image_url"),
            product_url=product_data.get("url"),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["chain", "source_product_id"],
            set_={
                "name": stmt.excluded.name,
                "brand": stmt.excluded.brand,
                "category": stmt.excluded.category,
                "abv_percent": stmt.excluded.abv_percent,
                "pack_count": stmt.excluded.pack_count,
                "unit_volume_ml": stmt.excluded.unit_volume_ml,
                "total_volume_ml": stmt.excluded.total_volume_ml,
                "image_url": stmt.excluded.image_url,
                "product_url": stmt.excluded.product_url,
                "updated_at": now,
            },
        )
        stmt = stmt.returning(Product.id)

        result = await session.execute(stmt)
        product_id = result.scalar_one()

        # For MVP: Create/update prices for all stores of this chain
        # In the future, this could be store-specific pricing
        for store in stores:
            # Check if price exists and has changed
            existing_price = await session.execute(
                select(Price).where(
                    Price.product_id == product_id, Price.store_id == store.id
                )
            )
            existing = existing_price.scalar_one_or_none()

            price_changed = False
            if existing:
                # Check if price has changed
                if (
                    existing.price_nzd != product_data["price_nzd"]
                    or existing.promo_price_nzd != product_data.get("promo_price_nzd")
                    or existing.is_member_only != product_data.get("is_member_only", False)
                ):
                    price_changed = True
                    changed = True

                # Update existing price
                existing.price_nzd = product_data["price_nzd"]
                existing.promo_price_nzd = product_data.get("promo_price_nzd")
                existing.promo_text = product_data.get("promo_text")
                existing.promo_ends_at = product_data.get("promo_ends_at")
                existing.is_member_only = product_data.get("is_member_only", False)
                existing.last_seen_at = now
                if price_changed:
                    existing.price_last_changed_at = now
            else:
                # Create new price
                changed = True
                price = Price(
                    product_id=product_id,
                    store_id=store.id,
                    price_nzd=product_data["price_nzd"],
                    promo_price_nzd=product_data.get("promo_price_nzd"),
                    promo_text=product_data.get("promo_text"),
                    promo_ends_at=product_data.get("promo_ends_at"),
                    is_member_only=product_data.get("is_member_only", False),
                    last_seen_at=now,
                    price_last_changed_at=now,
                )
                session.add(price)

        return changed

    @abc.abstractmethod
    async def fetch_catalog_pages(self) -> List[str]:
        raise NotImplementedError

    @abc.abstractmethod
    async def parse_products(self, payload: str) -> List[dict]:
        raise NotImplementedError


__all__ = ["Scraper"]
