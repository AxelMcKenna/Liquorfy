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

# Generic liquor type words that don't distinguish variants across chains.
# e.g. "Absolut Vodka 700ml" vs "Absolut 700ml" should share a canonical ID.
_BASE_TYPE_WORDS = frozenset({
    "vodka", "gin", "rum", "whisky", "whiskey", "bourbon", "scotch",
    "beer", "lager", "ale", "pilsner", "stout", "porter",
    "wine", "cider", "tequila", "brandy", "cognac",
    "spirits", "spirit", "liqueur", "rtd",
})


def _normalize_variant(variant: str) -> str:
    """Collapse base-type-only variants to empty string.

    Chains inconsistently include type words ("Vodka", "Lager") in names.
    Stripping them ensures the same product matches across chains regardless.
    """
    words = variant.split()
    if not words:
        return ""
    if all(w in _BASE_TYPE_WORDS for w in words):
        return ""
    while words and words[0] in _BASE_TYPE_WORDS:
        words.pop(0)
    while words and words[-1] in _BASE_TYPE_WORDS:
        words.pop()
    return " ".join(words)


def _extract_variant(name: str, brand: str) -> str:
    """Extract the variant/flavour descriptor from a product name.

    Strips brand, volume, pack count, ABV, common noise words, and pure
    base-type words to isolate what makes this product unique within the
    same brand+size.

    Examples:
        "Absolut Vodka Citron 700ml"  → "citron"
        "Absolut Passionfruit 700mL"  → "passionfruit"
        "Heineken Lager 330ml 12 Pack" → ""
        "Jack Daniel's Tennessee Whiskey 700ml" → "tennessee"
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
    # Collapse whitespace, trim, then normalize away pure base-type variants
    s = _MULTI_SPACE.sub(" ", s).strip()
    return _normalize_variant(s)


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

    Returns None if total_volume_ml or pack_count is missing, or if no
    usable brand can be derived from either the caller or the name.

    Hash inputs: brand | variant | total_volume_ml | pack_count | is_sugar_free.
    `category` is intentionally excluded — chains use incompatible category
    vocabularies (e.g. "Wine / Red Wine" vs "red_wine") and including it
    fragments otherwise-identical SKUs into different canonical IDs.
    `abv_percent` is excluded for the same reason — retailers inconsistently
    embed ABV in product names.

    The `category` and `abv_percent` parameters are kept for call-site
    compatibility but ignored.
    """
    del abv_percent, category  # accepted for compat; never hashed

    if total_volume_ml is None or pack_count is None:
        return None

    # Re-infer brand from name so the runtime matcher produces the same
    # canonical ID as the backfill (which always re-infers). Chains often
    # store brand inconsistently in the brand column.
    resolved_brand = brand
    if name:
        from app.services.parser_utils import infer_brand
        inferred = infer_brand(name)
        if inferred:
            resolved_brand = inferred

    if not resolved_brand:
        return None

    variant = _extract_variant(name, resolved_brand) if name else ""

    key = "|".join([
        resolved_brand.strip().lower(),
        variant,
        str(total_volume_ml),
        str(pack_count),
        str(bool(is_sugar_free)),
    ])
    return uuid.uuid5(_NAMESPACE, key)


def attach_canonical_id(product_data: dict) -> dict:
    """Populate `canonical_product_id` on a scraper product dict in place.

    Use this from scraper upsert paths that build raw product dicts directly
    (instead of going through `Scraper.build_product_dict`). Idempotent —
    safe to call on dicts that already carry a canonical id; it will be
    overwritten with the freshly-computed value so the matcher always runs.
    """
    product_data["canonical_product_id"] = compute_canonical_id(
        name=product_data.get("name"),
        brand=product_data.get("brand"),
        total_volume_ml=product_data.get("total_volume_ml"),
        pack_count=product_data.get("pack_count"),
        is_sugar_free=bool(product_data.get("is_sugar_free", False)),
    )
    return product_data
