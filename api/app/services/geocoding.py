"""Geocoding service to convert addresses to coordinates."""
from __future__ import annotations

import asyncio
import logging
from typing import Optional, Tuple
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

# Using Nominatim (OpenStreetMap) for free geocoding
# Rate limit: 1 request per second
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "Liquorfy/1.0 (Store Location Service; +https://liquorfy.co.nz)"


class GeocodeError(Exception):
    """Raised when geocoding fails."""
    pass


async def geocode_address(address: str, region: str = "New Zealand") -> Tuple[float, float]:
    """
    Geocode an address to latitude and longitude.

    Args:
        address: The address to geocode
        region: The region/country to search in (default: New Zealand)

    Returns:
        Tuple of (latitude, longitude)

    Raises:
        GeocodeError: If geocoding fails
    """
    full_address = f"{address}, {region}"

    params = {
        "q": full_address,
        "format": "json",
        "limit": 1,
        "countrycodes": "nz",  # Limit to New Zealand
    }

    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(NOMINATIM_URL, params=params, headers=headers)
            response.raise_for_status()

            results = response.json()

            if not results:
                raise GeocodeError(f"No results found for address: {full_address}")

            result = results[0]
            lat = float(result["lat"])
            lon = float(result["lon"])

            logger.info(f"Geocoded '{full_address}' to ({lat}, {lon})")
            return (lat, lon)

    except httpx.HTTPError as e:
        raise GeocodeError(f"HTTP error during geocoding: {e}")
    except (KeyError, ValueError, IndexError) as e:
        raise GeocodeError(f"Failed to parse geocoding response: {e}")


async def geocode_with_retry(
    address: str,
    region: str = "New Zealand",
    max_retries: int = 3,
    delay: float = 1.0
) -> Optional[Tuple[float, float]]:
    """
    Geocode an address with retry logic and rate limiting.

    Args:
        address: The address to geocode
        region: The region/country to search in
        max_retries: Maximum number of retry attempts
        delay: Delay between requests (for rate limiting)

    Returns:
        Tuple of (latitude, longitude) or None if all retries fail
    """
    for attempt in range(max_retries):
        try:
            # Rate limiting: wait before each request
            if attempt > 0:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s")
                await asyncio.sleep(wait_time)
            else:
                await asyncio.sleep(delay)  # Standard rate limit

            return await geocode_address(address, region)

        except GeocodeError as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to geocode '{address}' after {max_retries} attempts: {e}")
                return None
            else:
                logger.warning(f"Geocoding attempt {attempt + 1} failed: {e}")
                continue

    return None


__all__ = ["geocode_address", "geocode_with_retry", "GeocodeError"]
