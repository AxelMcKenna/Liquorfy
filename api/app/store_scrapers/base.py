"""Base class for store location scrapers."""
from __future__ import annotations

import abc
import logging
from typing import List, Dict, Any, Optional

from httpx import AsyncClient
from playwright.async_api import async_playwright, Browser, BrowserContext

logger = logging.getLogger(__name__)


class StoreLocationScraper(abc.ABC):
    """Base class for scraping store locations from liquor chain websites."""

    chain: str
    store_locator_url: str

    def __init__(self, use_browser: bool = False) -> None:
        """
        Initialize the store location scraper.

        Args:
            use_browser: If True, use Playwright browser for JavaScript-rendered content
        """
        self.client = AsyncClient(timeout=30)
        self.use_browser = use_browser
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None

        # Set respectful User-Agent
        self.client.headers.update({
            "User-Agent": "Liquorfy/1.0 (Store Location Service; +https://liquorfy.co.nz)"
        })

    async def __aenter__(self):
        """Context manager entry."""
        if self.use_browser:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(
                user_agent="Liquorfy/1.0 (Store Location Service; +https://liquorfy.co.nz)",
                viewport={"width": 1920, "height": 1080},
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        await self.client.aclose()

    @abc.abstractmethod
    async def fetch_stores(self) -> List[Dict[str, Any]]:
        """
        Fetch all store locations for this chain.

        Returns:
            List of store dictionaries with keys:
                - name: str (store name)
                - address: str (full address)
                - region: Optional[str] (region/city)
                - lat: Optional[float] (latitude, if available)
                - lon: Optional[float] (longitude, if available)
                - url: Optional[str] (store URL)
        """
        raise NotImplementedError


__all__ = ["StoreLocationScraper"]
