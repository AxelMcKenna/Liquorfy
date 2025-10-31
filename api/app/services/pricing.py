from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

STANDARD_DRINK_FACTOR = 0.789 / 0.010


@dataclass(frozen=True)
class PricingMetrics:
    price_per_100ml: Optional[float]
    standard_drinks: Optional[float]
    price_per_standard_drink: Optional[float]


def compute_pricing_metrics(
    *,
    total_volume_ml: Optional[float],
    abv_percent: Optional[float],
    effective_price_nzd: float,
) -> PricingMetrics:
    price_per_100ml: Optional[float] = None
    standard_drinks: Optional[float] = None
    price_per_standard_drink: Optional[float] = None

    if total_volume_ml and total_volume_ml > 0:
        price_per_100ml = round(effective_price_nzd / (total_volume_ml / 100), 2)

    if total_volume_ml and abv_percent:
        standard_drinks = round(
            (total_volume_ml / 1000) * (abv_percent / 100) * STANDARD_DRINK_FACTOR,
            2,
        )
        if standard_drinks > 0:
            price_per_standard_drink = round(effective_price_nzd / standard_drinks, 2)

    return PricingMetrics(
        price_per_100ml=price_per_100ml,
        standard_drinks=standard_drinks,
        price_per_standard_drink=price_per_standard_drink,
    )


__all__ = ["compute_pricing_metrics", "PricingMetrics"]
