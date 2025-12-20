from __future__ import annotations

import abc
import logging
from datetime import datetime
from typing import Iterable, List
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

                        for product_data in products:
                            try:
                                changed = await self._upsert_product_and_prices(
                                    session, product_data, stores
                                )
                                if changed:
                                    changed_items += 1
                            except Exception as e:
                                logger.error(f"Failed to persist product: {e}")
                                failed_items += 1

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
                ):
                    price_changed = True
                    changed = True

                # Update existing price
                existing.price_nzd = product_data["price_nzd"]
                existing.promo_price_nzd = product_data.get("promo_price_nzd")
                existing.promo_text = product_data.get("promo_text")
                existing.promo_ends_at = product_data.get("promo_ends_at")
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
