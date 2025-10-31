from app.services.pricing import compute_pricing_metrics


def test_compute_pricing_metrics():
    metrics = compute_pricing_metrics(total_volume_ml=1000, abv_percent=40, effective_price_nzd=50)
    assert metrics.price_per_100ml == 5.0
    assert metrics.standard_drinks is not None
    assert metrics.price_per_standard_drink is not None
