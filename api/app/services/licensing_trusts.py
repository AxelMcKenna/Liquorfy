"""Classify whether a store can legally sell alcohol under the West Auckland
Portage and Waitakere Licensing Trust monopoly.

Decision order for any store:
  1. STORE_OVERRIDES — explicit per-store entries (gold-standard truth, manually
     verified against Auckland Council GeoMaps).
  2. Trust-owned brand allowlist — if the store name matches a Trust-operated
     brand (West Liquor, The Tap, etc.) it's always allowed to sell alcohol.
  3. Point-in-polygon against PLT and WLT polygons (best-effort hand-digitised).
     Inside polygon ⇒ sells_alcohol=False unless brand is Trust-owned.

Stores within BOUNDARY_AMBIGUITY_BUFFER_DEG of either polygon edge are flagged
``needs_review=True`` so a human can verify against the official boundary.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Final, Optional

from app.data.licensing_trusts import (
    BOUNDARY_AMBIGUITY_BUFFER_DEG,
    PORTAGE_TRUST_POLYGON,
    WAITAKERE_TRUST_POLYGON,
)

logger = logging.getLogger(__name__)


PORTAGE: Final[str] = "portage"
WAITAKERE: Final[str] = "waitakere"


# Chain/name patterns operated by, or licensed through, the Trusts. These remain
# sells_alcohol=True even when geographically inside a Trust district because the
# Trust monopoly is held BY them, not against them.
# Source: thetrusts.co.nz retail brands.
_TRUST_OWNED_NAME_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"\bwest\s+liquor\b", re.I),
    re.compile(r"\bthe\s+tap\b", re.I),
    re.compile(r"\bvillage\s+wine\s*(&|and)?\s*spirits?\b", re.I),
    re.compile(r"\bliquor\s+spot\b", re.I),
    re.compile(r"\bhenderson\s+liquor\b", re.I),
    re.compile(r"\bthe\s+trusts?\b", re.I),
)


@dataclass(frozen=True)
class ClassificationResult:
    sells_alcohol: bool
    licensing_trust_area: Optional[str]   # "portage", "waitakere", or None
    needs_review: bool                    # True if the point is within the
                                          # ambiguity buffer of a polygon edge.
    reason: str                           # Human-readable audit string.


# Authoritative per-store overrides. Keyed by (chain, identifier_kind, identifier).
# identifier_kind is one of:
#   * "api_id" — match Store.api_id (e.g. Countdown numeric store IDs)
#   * "name"   — case-insensitive exact match on Store.name
#
# These were verified against the Trust district boundary one by one. If you add
# a new West Auckland supermarket to the seed data, add it here too and update
# the test fixture in api/app/tests/test_licensing_trusts.py.
def _override(trust: str, store_label: str) -> ClassificationResult:
    return ClassificationResult(
        sells_alcohol=False,
        licensing_trust_area=trust,
        needs_review=False,
        reason=f"{store_label} — {trust.title()} Licensing Trust district",
    )


# Authoritative per-store overrides. Each known West Auckland supermarket is
# registered TWICE: once by api_id (so auto-created scraper rows with the
# placeholder name "<chain> #<id>" still classify correctly) and once by the
# canonical store name (so name-based lookups during ingestion match too).
STORE_OVERRIDES: Final[dict[tuple[str, str, str], ClassificationResult]] = {}


def _register_override(*, chain: str, api_id: str, name: str, trust: str, label: str) -> None:
    result = _override(trust, label)
    STORE_OVERRIDES[(chain, "api_id", api_id)] = result
    STORE_OVERRIDES[(chain, "name", name.lower())] = result


# --- Countdown / Woolworths — Waitakere Licensing Trust ---
_register_override(chain="countdown", api_id="9038", name="Lincoln Road Woolworths",
                   trust=WAITAKERE, label="Lincoln Road Woolworths (Henderson)")
_register_override(chain="countdown", api_id="9064", name="Northwest Woolworths",
                   trust=WAITAKERE, label="Northwest Woolworths (Westgate/Massey)")
_register_override(chain="countdown", api_id="9147", name="Westgate Woolworths",
                   trust=WAITAKERE, label="Westgate Woolworths (Massey)")
_register_override(chain="countdown", api_id="9194", name="Henderson Woolworths",
                   trust=WAITAKERE, label="Henderson Woolworths")
_register_override(chain="countdown", api_id="9206", name="Te Atatu South Woolworths",
                   trust=WAITAKERE, label="Te Atatu South Woolworths")
_register_override(chain="countdown", api_id="9451", name="Te Atatu Woolworths",
                   trust=WAITAKERE, label="Te Atatu Peninsula Woolworths")
_register_override(chain="countdown", api_id="9551", name="Hobsonville Woolworths",
                   trust=WAITAKERE, label="Hobsonville Woolworths")

# --- Countdown / Woolworths — Portage Licensing Trust ---
_register_override(chain="countdown", api_id="9146", name="Kelston Woolworths",
                   trust=PORTAGE, label="Kelston Woolworths (Glen Eden)")
_register_override(chain="countdown", api_id="9149", name="Lynnmall Woolworths",
                   trust=PORTAGE, label="LynnMall Woolworths (New Lynn)")
_register_override(chain="countdown", api_id="9211", name="Blockhouse Bay Woolworths",
                   trust=PORTAGE, label="Blockhouse Bay Woolworths")

# --- PAK'nSAVE — Waitakere Licensing Trust ---
_register_override(chain="paknsave", api_id="6c73764e-b8e6-4e55-ad37-f6a9d207da1f",
                   name="PAK'nSAVE Alderman Dr Hen",
                   trust=WAITAKERE, label="PAK'nSAVE Alderman Drive (Henderson)")
_register_override(chain="paknsave", api_id="92086ded-a55d-4241-a364-7d7ea91531b4",
                   name="PAK'nSAVE Lincoln Road",
                   trust=WAITAKERE, label="PAK'nSAVE Lincoln Road (Henderson)")
_register_override(chain="paknsave", api_id="33d8d6fc-861a-45ff-9937-5ccdb55eaede",
                   name="PAK'nSAVE Westgate",
                   trust=WAITAKERE, label="PAK'nSAVE Westgate (Massey)")

# --- New World — Waitakere Licensing Trust ---
_register_override(chain="newworld", api_id="403b1c6f-121c-4945-8aa8-fa53a7e59133",
                   name="New World Hobsonville",
                   trust=WAITAKERE, label="New World Hobsonville")

# --- New World — Portage Licensing Trust ---
_register_override(chain="newworld", api_id="c8998066-d39b-401c-aa6b-d6d18f8d122f",
                   name="New World New Lynn",
                   trust=PORTAGE, label="New World New Lynn")
_register_override(chain="newworld", api_id="bfe3a4ae-2f6d-46ed-ba60-28451a4807bf",
                   name="New World Lincoln",
                   trust=PORTAGE, label="New World Lincoln (Henderson)")


def _point_in_polygon(lon: float, lat: float, polygon: list[tuple[float, float]]) -> bool:
    """Ray-casting point-in-polygon test. Polygon is a list of (lon, lat) tuples,
    closed (first == last). Returns True if the point is strictly inside.

    Standard even-odd rule. Robust enough for non-self-intersecting polygons; the
    Trust polygons are simple.
    """
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        # Check if the horizontal ray from (lon, lat) crosses edge (i,j).
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi
        ):
            inside = not inside
        j = i
    return inside


def _distance_to_polygon_edge(lon: float, lat: float, polygon: list[tuple[float, float]]) -> float:
    """Minimum 2-D distance (in degrees) from the point to any polygon edge.

    Degree distance is fine for ambiguity-buffer purposes — we don't need true
    geodesic. 0.002 deg ~ 220 m at NZ latitudes which is plenty for catching
    digitisation error.
    """
    min_d2 = float("inf")
    n = len(polygon)
    for i in range(n - 1):  # polygon is closed, so skip the duplicate last edge
        x1, y1 = polygon[i]
        x2, y2 = polygon[i + 1]
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            d2 = (lon - x1) ** 2 + (lat - y1) ** 2
        else:
            t = max(0.0, min(1.0, ((lon - x1) * dx + (lat - y1) * dy) / (dx * dx + dy * dy)))
            px, py = x1 + t * dx, y1 + t * dy
            d2 = (lon - px) ** 2 + (lat - py) ** 2
        if d2 < min_d2:
            min_d2 = d2
    return min_d2 ** 0.5


def _is_trust_owned_brand(store_name: str) -> bool:
    return any(p.search(store_name) for p in _TRUST_OWNED_NAME_PATTERNS)


def classify_store(
    *,
    chain: str,
    name: str,
    api_id: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
) -> ClassificationResult:
    """Classify a single store against the Trust monopoly rules.

    Returns a ClassificationResult. Stores with no coordinates AND no override
    AND no trust-owned name pattern default to ``sells_alcohol=True`` with
    ``needs_review=False`` — they can't be classified geographically so we trust
    them. This is the safe default because the supermarket chains we already
    have hardcoded overrides for cover every known West Auckland location.
    """
    chain_lc = (chain or "").lower()
    name_lc = (name or "").lower().strip()

    # 1. Per-store overrides win.
    if api_id is not None:
        hit = STORE_OVERRIDES.get((chain_lc, "api_id", str(api_id)))
        if hit is not None:
            return hit
    if name_lc:
        hit = STORE_OVERRIDES.get((chain_lc, "name", name_lc))
        if hit is not None:
            return hit

    # 2. Trust-owned brand — always allowed.
    if _is_trust_owned_brand(name or ""):
        return ClassificationResult(
            sells_alcohol=True,
            licensing_trust_area=None,
            needs_review=False,
            reason=f"Trust-owned brand: {name}",
        )

    # 3. Polygon classification — requires coordinates.
    if lat is None or lon is None:
        return ClassificationResult(
            sells_alcohol=True,
            licensing_trust_area=None,
            needs_review=False,
            reason="No coordinates available and no override; assumed outside Trust area",
        )

    in_waitakere = _point_in_polygon(lon, lat, WAITAKERE_TRUST_POLYGON)
    in_portage = _point_in_polygon(lon, lat, PORTAGE_TRUST_POLYGON)

    if in_waitakere or in_portage:
        # Inside a Trust polygon (and not a Trust-owned brand, checked above).
        trust = WAITAKERE if in_waitakere else PORTAGE
        # Edge check on the polygon the point falls inside.
        polygon = WAITAKERE_TRUST_POLYGON if in_waitakere else PORTAGE_TRUST_POLYGON
        edge_d = _distance_to_polygon_edge(lon, lat, polygon)
        needs_review = edge_d < BOUNDARY_AMBIGUITY_BUFFER_DEG
        return ClassificationResult(
            sells_alcohol=False,
            licensing_trust_area=trust,
            needs_review=needs_review,
            reason=(
                f"Inside {trust} Trust district polygon"
                + (" (near edge — review)" if needs_review else "")
            ),
        )

    # Outside both polygons — check whether we're close to an edge (potential
    # false negative from digitisation).
    edge_d_wlt = _distance_to_polygon_edge(lon, lat, WAITAKERE_TRUST_POLYGON)
    edge_d_plt = _distance_to_polygon_edge(lon, lat, PORTAGE_TRUST_POLYGON)
    near_edge = min(edge_d_wlt, edge_d_plt) < BOUNDARY_AMBIGUITY_BUFFER_DEG
    return ClassificationResult(
        sells_alcohol=True,
        licensing_trust_area=None,
        needs_review=near_edge,
        reason=(
            "Outside both Trust polygons"
            + (" (near edge — review)" if near_edge else "")
        ),
    )


__all__ = [
    "PORTAGE",
    "WAITAKERE",
    "ClassificationResult",
    "STORE_OVERRIDES",
    "classify_store",
]
