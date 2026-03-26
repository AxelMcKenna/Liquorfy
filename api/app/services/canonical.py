"""Deterministic canonical product ID for cross-chain matching."""

from __future__ import annotations

import uuid

# Fixed namespace for Liquorfy canonical product hashing
_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def compute_canonical_id(
    *,
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

    key = "|".join([
        brand.strip().lower(),
        str(total_volume_ml),
        str(pack_count),
        str(abv_percent) if abv_percent is not None else "NO_ABV",
        category.strip().lower() if category else "NO_CAT",
        str(is_sugar_free),
    ])
    return uuid.uuid5(_NAMESPACE, key)
