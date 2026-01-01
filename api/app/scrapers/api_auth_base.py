"""
Base class for API scrapers that require browser-based authentication.
Provides shared authentication and cookie/token extraction via Playwright.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from playwright.async_api import async_playwright

try:
    from undetected_playwright.tarnished import Malenia
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

logger = logging.getLogger(__name__)


class APIAuthBase:
    """
    Mixin class for API scrapers that need browser-based authentication.
    Provides shared authentication and cookie/token extraction via browser automation.

    This is useful for APIs that require:
    - Session cookies obtained through browser interaction
    - JWT tokens captured from network requests
    - Bypassing Cloudflare or other bot detection
    """

    # To be set by subclasses
    site_url: str = ""  # e.g., "https://www.countdown.co.nz"
    api_domain: str = ""  # e.g., "api-prod.newworld.co.nz" (for token capture)

    def __init__(self):
        self.auth_token: Optional[str] = None
        self.cookies: dict = {}

    async def _get_auth_via_browser(
        self,
        *,
        capture_token: bool = True,
        capture_cookies: bool = True,
        headless: bool = False,
        wait_time: float = 10.0
    ) -> Optional[str]:
        """
        Open browser to bypass bot detection and capture auth credentials.

        Args:
            capture_token: Whether to capture JWT token from network requests
            capture_cookies: Whether to capture session cookies
            headless: Run browser in headless mode (False recommended for Cloudflare)
            wait_time: Time to wait for API calls and cookies (seconds)

        Returns:
            Auth token if capture_token=True, else None
        """
        logger.info(f"Obtaining auth credentials via browser for {self.site_url}...")

        token = None

        async with async_playwright() as p:
            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ]

            browser = await p.chromium.launch(
                headless=headless,
                args=launch_args
            )

            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-NZ",
                timezone_id="Pacific/Auckland",
            )

            # Apply stealth if available
            if STEALTH_AVAILABLE:
                try:
                    await Malenia.apply_stealth(context)
                    logger.info("Stealth mode enabled")
                except Exception as e:
                    logger.warning(f"Failed to apply stealth: {e}")

            page = await context.new_page()

            # Capture token from network requests if requested
            if capture_token and self.api_domain:
                async def handle_request(route, request):
                    nonlocal token
                    if self.api_domain in request.url:
                        auth_header = request.headers.get("authorization")
                        if auth_header and auth_header.startswith("Bearer "):
                            if not token:
                                token = auth_header.replace("Bearer ", "")
                                logger.info(f"Captured auth token: {token[:50]}...")
                    await route.continue_()

                await page.route("**/*", handle_request)

            try:
                # Navigate to site
                await page.goto(
                    self.site_url,
                    wait_until="load",
                    timeout=60000
                )

                # Wait for potential Cloudflare challenge
                await asyncio.sleep(3)
                challenge = await page.query_selector('text="Just a moment"')
                if challenge:
                    logger.info("Waiting for Cloudflare challenge to resolve...")
                    for i in range(30):
                        await asyncio.sleep(1)
                        challenge = await page.query_selector('text="Just a moment"')
                        if not challenge:
                            logger.info("Cloudflare challenge resolved")
                            break

                # Wait for page to fully load and API calls to trigger
                await asyncio.sleep(wait_time)

                # Capture cookies if requested
                if capture_cookies:
                    browser_cookies = await context.cookies()
                    self.cookies = {cookie['name']: cookie['value'] for cookie in browser_cookies}
                    logger.info(f"Captured {len(self.cookies)} cookies")

            except Exception as e:
                logger.error(f"Error during browser auth: {e}")
            finally:
                await browser.close()

        return token


__all__ = ["APIAuthBase"]
