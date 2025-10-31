from __future__ import annotations

import abc
from typing import Iterable, List

from httpx import AsyncClient

from app.core.config import get_settings
from app.db.session import get_async_session

settings = get_settings()


class Scraper(abc.ABC):
    chain: str

    def __init__(self) -> None:
        self.client = AsyncClient(timeout=20)

    async def run(self) -> None:
        pages = await self.fetch_catalog_pages()
        async with get_async_session() as session:
            for page in pages:
                products = await self.parse_products(page)
                # For MVP we simply log count; persistence would go here
                _ = products

    @abc.abstractmethod
    async def fetch_catalog_pages(self) -> List[str]:
        raise NotImplementedError

    @abc.abstractmethod
    async def parse_products(self, payload: str) -> List[dict]:
        raise NotImplementedError


__all__ = ["Scraper"]
