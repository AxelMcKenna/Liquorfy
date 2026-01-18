"""Tests for pricing service."""
from __future__ import annotations

import pytest

from app.services.pricing import STANDARD_DRINK_FACTOR, PricingMetrics, compute_pricing_metrics


class TestComputePricingMetrics:
    """Tests for compute_pricing_metrics function."""

    def test_price_per_100ml_calculation(self):
        """Should correctly calculate price per 100ml."""
        metrics = compute_pricing_metrics(
            total_volume_ml=1000.0,
            abv_percent=None,
            effective_price_nzd=50.0
        )
        assert metrics.price_per_100ml == 5.0

    def test_price_per_100ml_with_small_volume(self):
        """Should calculate price per 100ml for small volumes."""
        metrics = compute_pricing_metrics(
            total_volume_ml=330.0,
            abv_percent=None,
            effective_price_nzd=9.99
        )
        assert metrics.price_per_100ml == pytest.approx(3.03, 0.01)

    def test_price_per_100ml_none_when_no_volume(self):
        """Should return None price per 100ml when volume is None."""
        metrics = compute_pricing_metrics(
            total_volume_ml=None,
            abv_percent=5.0,
            effective_price_nzd=29.99
        )
        assert metrics.price_per_100ml is None

    def test_price_per_100ml_none_when_zero_volume(self):
        """Should return None price per 100ml when volume is zero."""
        metrics = compute_pricing_metrics(
            total_volume_ml=0.0,
            abv_percent=5.0,
            effective_price_nzd=29.99
        )
        assert metrics.price_per_100ml is None

    def test_standard_drinks_calculation(self):
        """Should correctly calculate standard drinks."""
        # 1L of 40% spirit = 31.6 standard drinks (NZ definition)
        metrics = compute_pricing_metrics(
            total_volume_ml=1000.0,
            abv_percent=40.0,
            effective_price_nzd=50.0
        )
        assert metrics.standard_drinks is not None
        # NZ standard drink = 10g of alcohol
        # 1000ml * 0.40 * 0.789 g/ml / 10g = 31.56 drinks
        expected = (1000 / 1000) * (40 / 100) * STANDARD_DRINK_FACTOR
        assert metrics.standard_drinks == pytest.approx(expected, 0.1)

    def test_standard_drinks_beer(self):
        """Should calculate standard drinks for typical beer."""
        # 330ml at 5% = ~1.3 standard drinks
        metrics = compute_pricing_metrics(
            total_volume_ml=330.0,
            abv_percent=5.0,
            effective_price_nzd=5.0
        )
        assert metrics.standard_drinks is not None
        expected = (330 / 1000) * (5 / 100) * STANDARD_DRINK_FACTOR
        assert metrics.standard_drinks == pytest.approx(expected, 0.1)

    def test_standard_drinks_none_when_no_volume(self):
        """Should return None standard drinks when volume is None."""
        metrics = compute_pricing_metrics(
            total_volume_ml=None,
            abv_percent=5.0,
            effective_price_nzd=29.99
        )
        assert metrics.standard_drinks is None

    def test_standard_drinks_none_when_no_abv(self):
        """Should return None standard drinks when ABV is None."""
        metrics = compute_pricing_metrics(
            total_volume_ml=330.0,
            abv_percent=None,
            effective_price_nzd=5.0
        )
        assert metrics.standard_drinks is None

    def test_price_per_standard_drink(self):
        """Should correctly calculate price per standard drink."""
        # 1L of 40% at $50 = 31.6 drinks = ~$1.58 per drink
        metrics = compute_pricing_metrics(
            total_volume_ml=1000.0,
            abv_percent=40.0,
            effective_price_nzd=50.0
        )
        assert metrics.price_per_standard_drink is not None
        assert metrics.price_per_standard_drink > 0

    def test_price_per_standard_drink_none_when_zero_drinks(self):
        """Should return None when standard drinks would be zero."""
        metrics = compute_pricing_metrics(
            total_volume_ml=100.0,
            abv_percent=0.0,  # 0% ABV = 0 drinks
            effective_price_nzd=5.0
        )
        assert metrics.price_per_standard_drink is None

    def test_all_metrics_returned(self):
        """Should return all metrics when all inputs provided."""
        metrics = compute_pricing_metrics(
            total_volume_ml=700.0,
            abv_percent=37.5,
            effective_price_nzd=39.99
        )
        assert metrics.price_per_100ml is not None
        assert metrics.standard_drinks is not None
        assert metrics.price_per_standard_drink is not None

    def test_metrics_rounded_to_2_decimal(self):
        """Metrics should be rounded to 2 decimal places."""
        metrics = compute_pricing_metrics(
            total_volume_ml=333.0,  # Odd volume
            abv_percent=4.7,  # Odd ABV
            effective_price_nzd=7.77  # Odd price
        )
        if metrics.price_per_100ml is not None:
            assert metrics.price_per_100ml == round(metrics.price_per_100ml, 2)
        if metrics.standard_drinks is not None:
            assert metrics.standard_drinks == round(metrics.standard_drinks, 2)
        if metrics.price_per_standard_drink is not None:
            assert metrics.price_per_standard_drink == round(metrics.price_per_standard_drink, 2)


class TestPricingMetricsDataclass:
    """Tests for PricingMetrics dataclass."""

    def test_pricing_metrics_immutable(self):
        """PricingMetrics should be immutable (frozen)."""
        metrics = PricingMetrics(
            price_per_100ml=5.0,
            standard_drinks=1.3,
            price_per_standard_drink=3.85
        )
        with pytest.raises(AttributeError):
            metrics.price_per_100ml = 10.0

    def test_pricing_metrics_allows_none(self):
        """PricingMetrics should allow None values."""
        metrics = PricingMetrics(
            price_per_100ml=None,
            standard_drinks=None,
            price_per_standard_drink=None
        )
        assert metrics.price_per_100ml is None
        assert metrics.standard_drinks is None
        assert metrics.price_per_standard_drink is None


class TestStandardDrinkFactor:
    """Tests for standard drink calculation factor."""

    def test_standard_drink_factor_correct(self):
        """Standard drink factor should be correct for NZ definition."""
        # NZ: 1 standard drink = 10g pure alcohol
        # Alcohol density = 0.789 g/ml
        # Factor = 0.789 / 0.010 = 78.9
        assert STANDARD_DRINK_FACTOR == pytest.approx(78.9, 0.1)
