from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

STANDARD_DRINK_FACTOR = Decimal("78.9")
MONEY_QUANTUM = Decimal("0.01")


@dataclass(frozen=True)
class PricingMetrics:
    price_per_100ml: Optional[Decimal]
    standard_drinks: Optional[Decimal]
    price_per_standard_drink: Optional[Decimal]


def normalize_money(value: Decimal | float | int | str) -> Decimal:
    """Convert scraped or request money into an exact two-decimal value."""
    return Decimal(str(value)).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def compute_pricing_metrics(
    *,
    total_volume_ml: Optional[float],
    abv_percent: Optional[float],
    effective_price_nzd: Decimal | float,
) -> PricingMetrics:
    price = normalize_money(effective_price_nzd)
    price_per_100ml: Optional[Decimal] = None
    standard_drinks: Optional[Decimal] = None
    price_per_standard_drink: Optional[Decimal] = None

    if total_volume_ml and total_volume_ml > 0:
        volume = Decimal(str(total_volume_ml))
        price_per_100ml = (price / (volume / Decimal("100"))).quantize(
            MONEY_QUANTUM, rounding=ROUND_HALF_UP
        )

    if total_volume_ml and abv_percent:
        volume = Decimal(str(total_volume_ml))
        abv = Decimal(str(abv_percent))
        standard_drinks = (
            (volume / Decimal("1000"))
            * (abv / Decimal("100"))
            * STANDARD_DRINK_FACTOR
        ).quantize(
            MONEY_QUANTUM,
            rounding=ROUND_HALF_UP,
        )
        if standard_drinks > 0:
            price_per_standard_drink = (price / standard_drinks).quantize(
                MONEY_QUANTUM, rounding=ROUND_HALF_UP
            )

    return PricingMetrics(
        price_per_100ml=price_per_100ml,
        standard_drinks=standard_drinks,
        price_per_standard_drink=price_per_standard_drink,
    )


__all__ = [
    "compute_pricing_metrics",
    "normalize_money",
    "PricingMetrics",
    "STANDARD_DRINK_FACTOR",
]
