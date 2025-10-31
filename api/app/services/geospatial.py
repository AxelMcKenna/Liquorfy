from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def within_radius(
    *,
    stores: Sequence[Tuple[str, float, float]],
    lat: float,
    lon: float,
    radius_km: float,
) -> List[Tuple[str, float]]:
    """Return store ids and distances for stores within radius."""

    results: List[Tuple[str, float]] = []
    for store_id, store_lat, store_lon in stores:
        distance = haversine_distance(lat, lon, store_lat, store_lon)
        if distance <= radius_km:
            results.append((store_id, distance))
    results.sort(key=lambda item: item[1])
    return results


__all__ = ["haversine_distance", "within_radius"]
