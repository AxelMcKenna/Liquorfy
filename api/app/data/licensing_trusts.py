"""Hand-digitised boundary polygons for the Portage and Waitakere Licensing Trust districts.

Background
----------
Under the Sale and Supply of Alcohol Act 2012 (formerly the Sale of Liquor Act 1989
and originally the Licensing Trusts Act 1949), the Portage Licensing Trust (PLT) and
Waitakere Licensing Trust (WLT) hold exclusive off-licence and on-licence rights
within their gazetted districts in west Auckland. Supermarkets, bottle stores and
restaurants in those districts cannot sell alcohol unless the licence is held by the
Trust itself (West Liquor, The Tap, Village Wine & Spirits, etc.) or by a Trust
subsidiary.

The Trust district boundaries are gazetted but the polygon dataset is NOT published
publicly by LINZ, Stats NZ, Auckland Council Open Data, the Local Government
Commission, OpenStreetMap or Koordinates as of May 2026. The polygons below are
digitised from:

  * the documented suburb membership lists published by The Trusts
    (https://thetrusts.co.nz/about-your-trusts/),
  * the documented eastern boundary "west of Richardson Road and Boundary Road"
    in Avondale/Owairaka,
  * the Tasman Sea coastline (west), Manukau Harbour (south) and Waitemata Harbour
    (north/east) using public coastal waypoints.

These polygons are best-effort and may be off the gazetted line by tens of metres
in places. Where 100% correctness matters — i.e. for every known supermarket — the
``STORE_OVERRIDES`` table in ``app.services.licensing_trusts`` provides the
authoritative answer keyed by (chain, identifier) and is consulted before the
polygon. Any store falling within ~200 m of either polygon edge is flagged as
``needs_review`` so a human can verify it against Auckland Council GeoMaps before
the classification is trusted.
"""
from __future__ import annotations

from typing import Final


# --- Waitakere Licensing Trust (WLT) ---
# Covers (per The Trusts): Whenuapai, Hobsonville, West Harbour, Waitakere Township,
# Massey, Red Hills, Henderson, Ranui, Swanson, Taupaki, Te Atatu Peninsula,
# Te Atatu South, Sunnyvale, Oratia, Waiatarua, Karekare, Piha, Bethells Beach.
#
# Vertices are (lon, lat) in WGS84, ordered counterclockwise (GeoJSON spec for
# exterior ring). Polygon is closed (first == last).
WAITAKERE_TRUST_POLYGON: Final[list[tuple[float, float]]] = [
    # West coast - Tasman Sea, north to south along the Waitakere Ranges coast
    (174.4380, -36.8650),   # Muriwai south (boundary with Rodney)
    (174.4480, -36.8930),   # Bethells / Te Henga beach
    (174.4630, -36.9530),   # Piha beach
    (174.4810, -36.9920),   # Karekare beach
    (174.5300, -37.0470),   # Whatipu (mouth of Manukau Harbour) - shared with PLT here
    # Inland: cut north along the Waitakere Ranges spine, leaving PLT to the south.
    # WLT covers the ranges' interior (Waiatarua, Oratia) but excludes Titirangi/Laingholm.
    (174.5800, -36.9650),   # Waiatarua / Oratia ridge
    (174.6100, -36.9300),   # Henderson Valley / Oratia north edge
    (174.6450, -36.9050),   # Henderson east edge (Sturges Rd corridor)
    # Sunnyvale / Glendene border (Patiki Rd / Sturges Rd intersection area)
    (174.6500, -36.8950),
    # Te Atatu South / Edmonton border across the NW Motorway
    (174.6500, -36.8780),
    # Whau River mouth (NE corner of Te Atatu Peninsula)
    (174.6600, -36.8500),
    # Waitemata Harbour shore (north side of Te Atatu Peninsula / West Harbour)
    (174.6680, -36.8400),
    # West Harbour east edge (around Marina View)
    (174.6500, -36.8200),
    # Hobsonville Point ferry terminal
    (174.6680, -36.7920),
    # Hobsonville west / Whenuapai south
    (174.6400, -36.7800),
    # Whenuapai - RNZAF base south
    (174.6200, -36.7750),
    # Taupaki / Riverhead boundary (rural north edge of WLT)
    (174.5700, -36.7850),
    # Waitakere Township north
    (174.5300, -36.8200),
    # Back to start
    (174.4380, -36.8650),
]


# --- Portage Licensing Trust (PLT) ---
# Covers (per The Trusts): Glendene, Kelston, Glen Eden, Kaurilands, Titirangi,
# Laingholm, Parau, Cornwallis, Huia, Little Huia, Whatipu, Green Bay, New Lynn,
# Avondale, Waterview, Blockhouse Bay, New Windsor, Owairaka.
#
# Eastern boundary follows Richardson Road (Owairaka/Mt Roskill divide) and
# Boundary Road (Avondale/Mt Albert divide).
PORTAGE_TRUST_POLYGON: Final[list[tuple[float, float]]] = [
    # Whatipu (mouth of Manukau Harbour) - shared boundary with WLT to the north
    (174.5300, -37.0470),
    # Huia / Little Huia
    (174.5650, -37.0050),
    # Cornwallis / Parau
    (174.6000, -36.9850),
    # Laingholm
    (174.6200, -36.9700),
    # Titirangi
    (174.6500, -36.9450),
    # Kaurilands / Glen Eden south
    (174.6500, -36.9250),
    # Glen Eden / Kelston border
    (174.6500, -36.9050),
    # Glendene south - meets WLT here at Sunnyvale border (Patiki Rd area)
    (174.6500, -36.8950),
    # Whau Creek south (New Lynn east edge along the river)
    (174.6700, -36.9100),
    # Avondale north - Waterview boundary
    (174.7080, -36.8830),
    # Waterview - Great North Rd / Waterview tunnel area
    (174.7100, -36.8900),
    # Avondale east - Boundary Road (literal road name marking the boundary)
    (174.7120, -36.8980),
    # Owairaka east - Richardson Road
    (174.7130, -36.9100),
    # New Windsor / Owairaka south - Richardson Rd / Stoddard Rd
    (174.7100, -36.9250),
    # Blockhouse Bay east edge (Boundary Rd / Whitney St area)
    (174.7050, -36.9380),
    # Blockhouse Bay - Manukau Harbour coast
    (174.7000, -36.9500),
    # Green Bay coast
    (174.6750, -36.9550),
    # Titirangi south coast (Manukau Harbour)
    (174.6500, -36.9650),
    # Laingholm coast
    (174.6300, -36.9800),
    # Huia coast (Manukau Harbour)
    (174.5800, -37.0050),
    # Back to Whatipu
    (174.5300, -37.0470),
]


# A buffer (in degrees, ~1 deg lat = 111 km, so 0.002 deg ~ 220 m) around either
# polygon's edge inside which a store is flagged as "boundary-ambiguous" and a
# human review is required. This protects against my hand-digitisation error.
BOUNDARY_AMBIGUITY_BUFFER_DEG: Final[float] = 0.002


__all__ = [
    "WAITAKERE_TRUST_POLYGON",
    "PORTAGE_TRUST_POLYGON",
    "BOUNDARY_AMBIGUITY_BUFFER_DEG",
]
