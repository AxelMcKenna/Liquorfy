from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

VOLUME_PATTERN = re.compile(
    r"(?P<count>\d+)\s*[x×]\s*(?P<unit>\d+(?:\.\d+)?)\s*(?P<measure>ml|l)"
)
SINGLE_VOLUME_PATTERN = re.compile(r"(?P<unit>\d+(?:\.\d+)?)\s*(?P<measure>ml|l)")
ABV_PATTERN = re.compile(r"(?P<abv>\d{1,2}(?:\.\d+)?)\s*%")


@dataclass(frozen=True)
class ParsedVolume:
    pack_count: Optional[int]
    unit_volume_ml: Optional[float]
    total_volume_ml: Optional[float]


def parse_volume(text: str) -> ParsedVolume:
    normalized = text.lower().replace("litre", "l").replace("litres", "l")
    match = VOLUME_PATTERN.search(normalized)
    if match:
        count = int(match.group("count"))
        unit_value = float(match.group("unit"))
        measure = match.group("measure")
        unit_ml = unit_value * (1000 if measure == "l" else 1)
        return ParsedVolume(pack_count=count, unit_volume_ml=unit_ml, total_volume_ml=count * unit_ml)
    match = SINGLE_VOLUME_PATTERN.search(normalized)
    if match:
        unit_value = float(match.group("unit"))
        measure = match.group("measure")
        unit_ml = unit_value * (1000 if measure == "l" else 1)
        return ParsedVolume(pack_count=None, unit_volume_ml=unit_ml, total_volume_ml=unit_ml)
    return ParsedVolume(pack_count=None, unit_volume_ml=None, total_volume_ml=None)


def extract_abv(text: str) -> Optional[float]:
    match = ABV_PATTERN.search(text)
    if match:
        return float(match.group("abv"))
    return None


__all__ = ["parse_volume", "ParsedVolume", "extract_abv"]
