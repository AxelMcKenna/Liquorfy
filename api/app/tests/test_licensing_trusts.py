"""Tests for the West Auckland Licensing Trust classifier.

Every known supermarket inside a Trust district MUST be classified as
sells_alcohol=False, and adjacent supermarkets outside the Trust must remain
sells_alcohol=True. The override table guarantees the former; the polygon
classifier handles the latter.
"""
from __future__ import annotations

import pytest

from app.services.licensing_trusts import (
    PORTAGE,
    WAITAKERE,
    classify_store,
)


# --- (chain, name, api_id, lat, lon, expected_sells_alcohol, expected_trust) ---

# Every known West Auckland supermarket. Coordinates are approximate store
# centroids — the override table classifies them by chain+name regardless, so
# coordinates here are advisory only.
WEST_AUCKLAND_SUPERMARKETS = [
    # Countdown / Woolworths — Waitakere Licensing Trust
    ("countdown", "Lincoln Road Woolworths",     "9038", -36.876, 174.629, False, WAITAKERE),
    ("countdown", "Northwest Woolworths",        "9064", -36.808, 174.601, False, WAITAKERE),
    ("countdown", "Westgate Woolworths",         "9147", -36.812, 174.608, False, WAITAKERE),
    ("countdown", "Henderson Woolworths",        "9194", -36.879, 174.633, False, WAITAKERE),
    ("countdown", "Te Atatu South Woolworths",   "9206", -36.873, 174.652, False, WAITAKERE),
    ("countdown", "Te Atatu Woolworths",         "9451", -36.851, 174.654, False, WAITAKERE),
    ("countdown", "Hobsonville Woolworths",      "9551", -36.795, 174.660, False, WAITAKERE),
    # Countdown / Woolworths — Portage Licensing Trust
    ("countdown", "Kelston Woolworths",          "9146", -36.901, 174.654, False, PORTAGE),
    ("countdown", "Lynnmall Woolworths",         "9149", -36.908, 174.682, False, PORTAGE),
    ("countdown", "Blockhouse Bay Woolworths",   "9211", -36.929, 174.704, False, PORTAGE),
    # PAK'nSAVE — Waitakere Licensing Trust (data file uses abbreviated names)
    ("paknsave", "PAK'nSAVE Alderman Dr Hen", "6c73764e-b8e6-4e55-ad37-f6a9d207da1f",
                                                  -36.879, 174.632, False, WAITAKERE),
    ("paknsave", "PAK'nSAVE Lincoln Road",   "92086ded-a55d-4241-a364-7d7ea91531b4",
                                                  -36.875, 174.630, False, WAITAKERE),
    ("paknsave", "PAK'nSAVE Westgate",       "33d8d6fc-861a-45ff-9937-5ccdb55eaede",
                                                  -36.811, 174.607, False, WAITAKERE),
    # New World — both Trusts
    ("newworld", "New World Hobsonville",    "403b1c6f-121c-4945-8aa8-fa53a7e59133",
                                                  -36.795, 174.660, False, WAITAKERE),
    ("newworld", "New World New Lynn",       "c8998066-d39b-401c-aa6b-d6d18f8d122f",
                                                  -36.908, 174.685, False, PORTAGE),
    ("newworld", "New World Lincoln",        "bfe3a4ae-2f6d-46ed-ba60-28451a4807bf",
                                                  -36.876, 174.629, False, PORTAGE),
]


# Same set, but classified using ONLY the placeholder name the scraper auto-creates
# ("<chain> #<api_id>"). This exercises the api_id override path which is the
# primary classification route for newly-discovered stores.
WEST_AUCKLAND_SUPERMARKETS_BY_PLACEHOLDER = [
    ("countdown", "countdown #9038", "9038", WAITAKERE),
    ("countdown", "countdown #9064", "9064", WAITAKERE),
    ("countdown", "countdown #9147", "9147", WAITAKERE),
    ("countdown", "countdown #9194", "9194", WAITAKERE),
    ("countdown", "countdown #9206", "9206", WAITAKERE),
    ("countdown", "countdown #9451", "9451", WAITAKERE),
    ("countdown", "countdown #9551", "9551", WAITAKERE),
    ("countdown", "countdown #9146", "9146", PORTAGE),
    ("countdown", "countdown #9149", "9149", PORTAGE),
    ("countdown", "countdown #9211", "9211", PORTAGE),
    ("paknsave", "paknsave #x", "6c73764e-b8e6-4e55-ad37-f6a9d207da1f", WAITAKERE),
    ("paknsave", "paknsave #x", "92086ded-a55d-4241-a364-7d7ea91531b4", WAITAKERE),
    ("paknsave", "paknsave #x", "33d8d6fc-861a-45ff-9937-5ccdb55eaede", WAITAKERE),
    ("newworld", "newworld #x", "403b1c6f-121c-4945-8aa8-fa53a7e59133", WAITAKERE),
    ("newworld", "newworld #x", "c8998066-d39b-401c-aa6b-d6d18f8d122f", PORTAGE),
    ("newworld", "newworld #x", "bfe3a4ae-2f6d-46ed-ba60-28451a4807bf", PORTAGE),
]


# Supermarkets adjacent to but outside the Trust districts. Must remain selling.
EAST_AUCKLAND_SUPERMARKETS_OUT_OF_TRUST = [
    # All east of Boundary Rd / Richardson Rd, definitely outside PLT.
    ("countdown", "St Lukes Woolworths",         -36.890, 174.725, True),
    ("countdown", "Mount Roskill Woolworths",    -36.917, 174.737, True),
    ("countdown", "Lynfield Woolworths",         -36.929, 174.722, True),
    ("countdown", "Pt Chevalier Woolworths",     -36.866, 174.706, True),
    ("countdown", "Grey Lynn Woolworths",        -36.866, 174.733, True),
    # North Shore — never in either Trust.
    ("countdown", "Glenfield Woolworths",        -36.785, 174.722, True),
    ("countdown", "Birkenhead Woolworths",       -36.806, 174.728, True),
    # South Auckland — never in either Trust.
    ("countdown", "Manukau Woolworths",          -36.991, 174.879, True),
]


# Trust-operated brands inside the Trust area MUST still sell alcohol (they ARE
# the licence holder). These are exempt regardless of polygon membership.
TRUST_OWNED_STORES = [
    ("west_liquor", "West Liquor Henderson",  -36.879, 174.633, True),
    ("west_liquor", "West Liquor Te Atatu",   -36.851, 174.654, True),
    ("the_tap",     "The Tap Glen Eden",      -36.913, 174.652, True),
    ("village",     "Village Wine & Spirits Titirangi", -36.937, 174.651, True),
]


@pytest.mark.parametrize(
    "chain,name,api_id,lat,lon,expected_sells,expected_trust",
    WEST_AUCKLAND_SUPERMARKETS,
)
def test_west_auckland_supermarket_cannot_sell_alcohol(
    chain, name, api_id, lat, lon, expected_sells, expected_trust
):
    result = classify_store(chain=chain, name=name, api_id=api_id, lat=lat, lon=lon)
    assert result.sells_alcohol is expected_sells, (
        f"{name}: expected sells_alcohol={expected_sells}, got {result.sells_alcohol} "
        f"({result.reason})"
    )
    assert result.licensing_trust_area == expected_trust, (
        f"{name}: expected trust={expected_trust}, got {result.licensing_trust_area}"
    )


@pytest.mark.parametrize(
    "chain,placeholder_name,api_id,expected_trust",
    WEST_AUCKLAND_SUPERMARKETS_BY_PLACEHOLDER,
)
def test_scraper_placeholder_name_classifies_by_api_id(
    chain, placeholder_name, api_id, expected_trust
):
    """When the scraper auto-creates a store, the name is '<chain> #<api_id>'.
    Classification must still flag known West Auckland supermarkets via api_id."""
    result = classify_store(chain=chain, name=placeholder_name, api_id=api_id)
    assert result.sells_alcohol is False, (
        f"placeholder {placeholder_name} (api_id={api_id}): expected sells_alcohol=False, "
        f"got {result.sells_alcohol} ({result.reason})"
    )
    assert result.licensing_trust_area == expected_trust


@pytest.mark.parametrize(
    "chain,name,lat,lon,expected_sells",
    EAST_AUCKLAND_SUPERMARKETS_OUT_OF_TRUST,
)
def test_supermarket_outside_trust_can_sell_alcohol(chain, name, lat, lon, expected_sells):
    result = classify_store(chain=chain, name=name, lat=lat, lon=lon)
    assert result.sells_alcohol is expected_sells, (
        f"{name}: expected sells_alcohol={expected_sells}, got {result.sells_alcohol} "
        f"({result.reason})"
    )
    assert result.licensing_trust_area is None


@pytest.mark.parametrize("chain,name,lat,lon,expected_sells", TRUST_OWNED_STORES)
def test_trust_owned_brand_can_sell_alcohol_in_trust_area(
    chain, name, lat, lon, expected_sells
):
    result = classify_store(chain=chain, name=name, lat=lat, lon=lon)
    assert result.sells_alcohol is expected_sells, (
        f"{name}: expected sells_alcohol={expected_sells}, got {result.sells_alcohol} "
        f"({result.reason})"
    )


def test_store_with_no_coordinates_and_no_override_defaults_to_selling():
    """Safe default: if we can't classify, assume the store sells alcohol.
    This is correct because all known West Auckland supermarkets are in the
    override table — a store reaching this branch is one we have no reason to
    suspect."""
    result = classify_store(chain="some_chain", name="Some Store", lat=None, lon=None)
    assert result.sells_alcohol is True
    assert result.licensing_trust_area is None


def test_override_table_wins_over_polygon():
    """Even if coordinates would put a store outside the polygon, an explicit
    override is honoured (audit trail)."""
    # Hobsonville Woolworths override exists; use coordinates clearly outside any
    # polygon (Wellington).
    result = classify_store(
        chain="countdown", name="Hobsonville Woolworths", api_id="9551",
        lat=-41.286, lon=174.776,
    )
    assert result.sells_alcohol is False
    assert result.licensing_trust_area == WAITAKERE


def test_point_in_polygon_handles_polygon_corners():
    """Stores near polygon vertices shouldn't crash and should produce a
    deterministic answer."""
    from app.data.licensing_trusts import WAITAKERE_TRUST_POLYGON
    vx, vy = WAITAKERE_TRUST_POLYGON[3]  # arbitrary vertex
    # Just below the vertex — should not error.
    result = classify_store(chain="x", name="y", lat=vy - 0.001, lon=vx)
    assert result.sells_alcohol in (True, False)


def test_chain_case_insensitivity():
    """Overrides are keyed lowercase; mixed-case chain inputs must still match."""
    result = classify_store(chain="Countdown", name="Henderson Woolworths")
    assert result.sells_alcohol is False
    assert result.licensing_trust_area == WAITAKERE
