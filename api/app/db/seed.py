from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import delete

from app.db.models import Price, Product, Store
from app.db.session import get_async_session

CHAINS = ["countdown", "new_world", "paknsave", "liquorland", "super_liquor", "bottle_o", "liquor_centre", "glengarry"]
CATEGORIES = ["beer", "wine", "spirits", "rtd", "cider"]
BRANDS = ["Heineken", "Corona", "Gordon's", "Absolut", "Somersby", "Jameson", "Moet"]


async def seed() -> None:
    async with get_async_session() as session:
        await session.execute(delete(Price))
        await session.execute(delete(Product))
        await session.execute(delete(Store))
        stores = []
        for chain in CHAINS:
            for index in range(3):
                store = Store(
                    id=uuid4(),
                    name=f"{chain.title()} Store {index+1}",
                    chain=chain,
                    lat=-36.85 + random.uniform(-0.5, 0.5),
                    lon=174.76 + random.uniform(-0.5, 0.5),
                    address=f"{100+index} Example Street",
                    region="Auckland",
                )
                session.add(store)
                stores.append(store)
        await session.flush()

        for i in range(60):
            chain = random.choice(CHAINS)
            brand = random.choice(BRANDS)
            category = random.choice(CATEGORIES)
            pack_count = random.choice([None, 6, 10, 12, 24])
            unit_volume_ml = random.choice([330, 500, 700, 1000])
            total_volume = (pack_count or 1) * unit_volume_ml
            abv = random.choice([None, 4.5, 5.0, 13.0, 37.0])
            product = Product(
                id=uuid4(),
                chain=chain,
                source_product_id=f"seed-{i}",
                name=f"{brand} {category.title()} #{i}",
                brand=brand,
                category=category,
                abv_percent=abv,
                pack_count=pack_count,
                unit_volume_ml=unit_volume_ml,
                total_volume_ml=total_volume,
            )
            session.add(product)
            store = random.choice([s for s in stores if s.chain == chain])
            price_value = random.uniform(15.0, 80.0)
            promo_price = price_value * 0.9 if random.random() < 0.3 else None
            price = Price(
                id=uuid4(),
                product_id=product.id,
                store_id=store.id,
                price_nzd=round(price_value, 2),
                promo_price_nzd=round(promo_price, 2) if promo_price else None,
                promo_text="10% off" if promo_price else None,
                last_seen_at=datetime.now(timezone.utc),
                price_last_changed_at=datetime.now(timezone.utc),
                is_member_only=False,
            )
            session.add(price)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
