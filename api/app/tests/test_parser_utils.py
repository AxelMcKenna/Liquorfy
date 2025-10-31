from app.services.parser_utils import ParsedVolume, extract_abv, parse_volume


def test_parse_single_volume():
    volume = parse_volume("Gordon's Gin 1L")
    assert volume.total_volume_ml == 1000
    assert volume.pack_count is None


def test_parse_multi_pack():
    volume = parse_volume("Heineken 24 × 330ml")
    assert volume.pack_count == 24
    assert volume.unit_volume_ml == 330
    assert volume.total_volume_ml == 24 * 330


def test_extract_abv():
    assert extract_abv("7% Vodka") == 7.0
    assert extract_abv("No abv") is None
