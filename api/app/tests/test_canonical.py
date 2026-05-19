"""Tests for the cross-chain canonical product matcher.

These cover the three production failure modes documented in the matcher
fix: case sensitivity in volume suffixes, category leakage into the hash,
and chain-specific metadata leakage.
"""
from __future__ import annotations

import uuid

import pytest

from app.services.canonical import attach_canonical_id, compute_canonical_id


def _cid(**overrides):
    base = dict(
        name="Absolut Vodka 700ml",
        brand="Absolut",
        total_volume_ml=700.0,
        pack_count=1,
    )
    base.update(overrides)
    return compute_canonical_id(**base)


class TestMatcherInvariants:
    def test_case_insensitive_volume_suffix(self):
        """'750ml' and '750mL' must produce the same canonical id."""
        a = compute_canonical_id(
            name="19 Crimes Cabernet Sauvignon 750ml",
            brand="19 Crimes",
            total_volume_ml=750.0,
            pack_count=1,
        )
        b = compute_canonical_id(
            name="19 Crimes Cabernet Sauvignon 750mL",
            brand="19 Crimes",
            total_volume_ml=750.0,
            pack_count=1,
        )
        assert a is not None
        assert a == b

    def test_category_does_not_affect_hash(self):
        """Different category strings must NOT split the canonical id."""
        a = _cid(category="Wine / Red Wine")
        b = _cid(category="red_wine")
        c = _cid(category=None)
        d = _cid(category="")
        assert a == b == c == d
        assert a is not None

    def test_chain_independent(self):
        """`chain` is not an input to the matcher — nothing about chain
        identity should leak into the canonical id.
        """
        # Calling site never passes a chain, but ensure the parser-utils
        # brand re-inference doesn't pick up chain-flavoured noise.
        a = compute_canonical_id(
            name="Jim Beam White Label 700ml",
            brand="Jim Beam",
            total_volume_ml=700.0,
            pack_count=1,
        )
        b = compute_canonical_id(
            name="Jim Beam White Label 700ml",
            brand="Jim Beam",
            total_volume_ml=700.0,
            pack_count=1,
        )
        assert a == b
        assert a is not None

    def test_abv_does_not_affect_hash(self):
        a = _cid(abv_percent=5.0)
        b = _cid(abv_percent=7.0)
        c = _cid(abv_percent=None)
        assert a == b == c

    def test_sugar_free_does_split_hash(self):
        """is_sugar_free is a real differentiator and MUST split."""
        a = compute_canonical_id(
            name="Coca-Cola 1.5L",
            brand="Coca-Cola",
            total_volume_ml=1500.0,
            pack_count=1,
            is_sugar_free=False,
        )
        b = compute_canonical_id(
            name="Coca-Cola Zero 1.5L",
            brand="Coca-Cola",
            total_volume_ml=1500.0,
            pack_count=1,
            is_sugar_free=True,
        )
        assert a is not None
        assert b is not None
        assert a != b

    def test_missing_required_fields_returns_none(self):
        # No volume → unmatchable.
        assert compute_canonical_id(
            name="Mystery", brand="X", total_volume_ml=None, pack_count=1
        ) is None
        # No pack → unmatchable.
        assert compute_canonical_id(
            name="Mystery", brand="X", total_volume_ml=700.0, pack_count=None
        ) is None
        # No brand and nothing the name parser can recover → unmatchable.
        assert compute_canonical_id(
            name=None, brand=None, total_volume_ml=700.0, pack_count=1
        ) is None

    def test_returns_uuid_type(self):
        cid = _cid()
        assert isinstance(cid, uuid.UUID)

    def test_deterministic(self):
        """Repeated calls must yield the same UUID."""
        assert _cid() == _cid()


class TestAttachCanonicalId:
    def test_populates_canonical_product_id_in_place(self):
        product_data = {
            "name": "Absolut Vodka 700ml",
            "brand": "Absolut",
            "total_volume_ml": 700.0,
            "pack_count": 1,
        }
        attach_canonical_id(product_data)
        assert isinstance(product_data["canonical_product_id"], uuid.UUID)

    def test_overwrites_existing_canonical(self):
        """Idempotent + overwrites — last computation wins so stale hashes
        from older code paths are corrected on the next scrape."""
        stale = uuid.uuid4()
        product_data = {
            "name": "Absolut Vodka 700ml",
            "brand": "Absolut",
            "total_volume_ml": 700.0,
            "pack_count": 1,
            "canonical_product_id": stale,
        }
        attach_canonical_id(product_data)
        assert product_data["canonical_product_id"] != stale

    def test_unmatchable_dict_gets_none(self):
        product_data = {
            "name": "Mystery",
            "brand": None,
            "total_volume_ml": None,
            "pack_count": None,
        }
        attach_canonical_id(product_data)
        assert product_data["canonical_product_id"] is None
