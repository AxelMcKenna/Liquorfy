"""Deterministic canonical product ID for cross-chain matching."""

from __future__ import annotations

import re
import uuid

# Fixed namespace for Liquorfy canonical product hashing
_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

# Patterns to strip from product names to extract the variant descriptor
_VOLUME_RE = re.compile(
    r"\d+\s*[x×]\s*\d+(?:\.\d+)?\s*(?:ml|cl|l|ltr|litre|litres|liters)\b"
    r"|\d+(?:\.\d+)?\s*(?:ml|cl|l|ltr|litre|litres|liters)\b",
    re.IGNORECASE,
)
_PACK_RE = re.compile(r"\b\d+\s*(?:pack|pk|cans?|bottles?|btls?)\b", re.IGNORECASE)
_ABV_RE = re.compile(r"\b\d{1,2}(?:\.\d+)?\s*%")
_NOISE_RE = re.compile(r"\b(?:premium|classic|original|imported|range|nz|new zealand)\b", re.IGNORECASE)
_MULTI_SPACE = re.compile(r"\s+")


def _extract_variant(name: str, brand: str) -> str:
    """Extract the variant/flavour descriptor from a product name.

    Strips brand, volume, pack count, ABV, and common noise words to
    isolate what makes this product unique within the same brand+size.

    Examples:
        "Absolut Vodka Citron 700ml"  → "vodka citron"
        "Absolut Passionfruit 700mL"  → "passionfruit"
        "Heineken Lager 330ml 12 Pack" → "lager"
        "Jack Daniel's Tennessee Whiskey 700ml" → "tennessee whiskey"
    """
    s = name.lower()
    # Strip brand (may appear as multi-word like "Jack Daniel's")
    brand_lower = brand.strip().lower()
    s = s.replace(brand_lower, "", 1)
    # Strip volume, pack, ABV, noise
    s = _VOLUME_RE.sub("", s)
    s = _PACK_RE.sub("", s)
    s = _ABV_RE.sub("", s)
    s = _NOISE_RE.sub("", s)
    # Collapse whitespace and trim
    s = _MULTI_SPACE.sub(" ", s).strip()
    return s


def compute_canonical_id(
    *,
    name: str | None = None,
    brand: str | None,
    total_volume_ml: float | None,
    pack_count: int | None,
    abv_percent: float | None = None,
    category: str | None = None,
    is_sugar_free: bool = False,
) -> uuid.UUID | None:
    """Compute a deterministic UUID v5 for cross-chain product matching.

    Products with the same canonical ID are considered the same physical
    product across different retail chains.

    Returns None if any required field (brand, total_volume_ml, pack_count)
    is missing — those products cannot be reliably matched.
    """
    if brand is None or total_volume_ml is None or pack_count is None:
        return None

    variant = _extract_variant(name, brand) if name else ""

    # ABV is intentionally excluded from the key because retailers
    # inconsistently include it in product names, causing the same product
    # to get different canonical IDs across chains.  Genuine ABV-based
    # variants (e.g. "5%" vs "7%") are rare for otherwise-identical names;
    # the variant descriptor handles meaningful differences.
    key = "|".join([
        brand.strip().lower(),
        variant,
        str(total_volume_ml),
        str(pack_count),
        category.strip().lower() if category else "NO_CAT",
        str(is_sugar_free),
    ])
    return uuid.uuid5(_NAMESPACE, key)
