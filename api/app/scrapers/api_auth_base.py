"""
Base class for API scrapers that require browser-based authentication.
Provides shared authentication and cookie/token extraction via Playwright.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
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

    @staticmethod
    def _normalize_token(raw: object) -> Optional[str]:
        """Normalize token candidates from headers/storage/cookies."""
        if raw is None:
            return None

        value = str(raw).strip().strip('"').strip("'")
        if not value:
            return None

        if value.lower().startswith("bearer "):
            value = value[7:].strip()

        # Common JWT shape
        if re.fullmatch(r"[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+", value):
            return value

        # Sometimes token is nested as JSON payload in storage.
        if value.startswith("{") and value.endswith("}"):
            try:
                parsed = json.loads(value)
            except Exception:
                parsed = None
            if isinstance(parsed, dict):
                for key in ("accessToken", "access_token", "token", "jwt", "idToken", "id_token"):
                    nested = APIAuthBase._normalize_token(parsed.get(key))
                    if nested:
                        return nested

        # Fallback for opaque long tokens
        if " " not in value and len(value) >= 32:
            return value

        return None

    @staticmethod
    def _extract_token_from_mapping(mapping: dict) -> tuple[Optional[str], Optional[str]]:
        """Extract token from key/value mapping, returning (token, source_key)."""
        if not mapping:
            return None, None

        preferred_keys = (
            "__nw_access_token__",
            "__ps_access_token__",
            "access_token",
            "accessToken",
            "token",
            "jwt",
            "id_token",
            "idToken",
        )

        for key in preferred_keys:
            if key in mapping:
                token = APIAuthBase._normalize_token(mapping.get(key))
                if token:
                    return token, key

        for key, value in mapping.items():
            key_l = str(key).lower()
            if any(marker in key_l for marker in ("token", "auth", "jwt", "bearer")):
                token = APIAuthBase._normalize_token(value)
                if token:
                    return token, str(key)

        return None, None

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
                def maybe_capture_from_headers(headers: dict, source: str) -> None:
                    nonlocal token
                    if token:
                        return
                    auth_header = headers.get("authorization") or headers.get("Authorization")
                    normalized = self._normalize_token(auth_header)
                    if normalized:
                        token = normalized
                        logger.info(f"Captured auth token from {source}: {token[:50]}...")

                def on_request(request) -> None:
                    if self.api_domain in request.url:
                        maybe_capture_from_headers(request.headers, f"request {request.url}")

                def on_response(response) -> None:
                    if self.api_domain in response.url:
                        maybe_capture_from_headers(response.request.headers, f"response request {response.url}")
                        maybe_capture_from_headers(response.headers, f"response headers {response.url}")

                page.on("request", on_request)
                page.on("response", on_response)

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

                # Fallback: extract token from local/session storage
                if capture_token and not token:
                    try:
                        storage = await page.evaluate("""() => ({
                            local: Object.fromEntries(Object.entries(window.localStorage)),
                            session: Object.fromEntries(Object.entries(window.sessionStorage))
                        })""")
                    except Exception as e:
                        storage = {}
                        logger.debug(f"Failed reading browser storage for token extraction: {e}")

                    local_token, local_key = self._extract_token_from_mapping(storage.get("local", {}))
                    session_token, session_key = self._extract_token_from_mapping(storage.get("session", {}))
                    token = local_token or session_token

                    if token:
                        if local_token:
                            logger.info(f"Captured auth token from localStorage key '{local_key}'")
                        else:
                            logger.info(f"Captured auth token from sessionStorage key '{session_key}'")

                # Capture cookies if requested
                if capture_cookies:
                    browser_cookies = await context.cookies()
                    self.cookies = {cookie['name']: cookie['value'] for cookie in browser_cookies}
                    logger.info(f"Captured {len(self.cookies)} cookies")

                    # Last fallback: token-like cookie values
                    if capture_token and not token:
                        cookie_token, cookie_key = self._extract_token_from_mapping(self.cookies)
                        if cookie_token:
                            token = cookie_token
                            logger.info(f"Captured auth token from cookie '{cookie_key}'")

            except Exception as e:
                logger.error(f"Error during browser auth: {e}")
            finally:
                await browser.close()

        return token


__all__ = ["APIAuthBase"]
