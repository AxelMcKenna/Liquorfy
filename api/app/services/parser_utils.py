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


# Known brands (common NZ liquor brands)
KNOWN_BRANDS = [
    # Beer
    "Heineken", "Corona", "Stella Artois", "Budweiser", "Miller", "Carlsberg",
    "Guinness", "Peroni", "Asahi", "Kirin", "Sapporo", "Tiger", "Chang",
    "Tui", "Speight's", "DB", "Export Gold", "Lion Red", "Steinlager",
    "Monteiths", "Mac's", "Tuatara", "Garage Project", "Panhead", "Emerson's",
    "Good George", "Behemoth", "Epic", "Parrotdog", "Fork & Brewer",

    # Wine
    "Cloudy Bay", "Kim Crawford", "Oyster Bay", "Villa Maria", "Brancott",
    "Matua", "Nobilo", "Saint Clair", "Delegat", "Yealands", "Marlborough",
    "Wither Hills", "Monkey Bay", "Stoneleigh", "Whitehaven", "Invivo",

    # Spirits
    "Gordon's", "Bombay", "Tanqueray", "Beefeater", "Hendrick's",
    "Smirnoff", "Absolut", "Grey Goose", "Belvedere", "Ketel One",
    "Bacardi", "Captain Morgan", "Havana Club", "Malibu", "Kraken",
    "Jack Daniel's", "Jim Beam", "Johnnie Walker", "Jameson", "Chivas",
    "Glenfiddich", "Glenlivet", "Monkey Shoulder", "Famous Grouse",
    "Jose Cuervo", "Patron", "1800", "Sauza", "El Jimador",
    "Baileys", "Kahlua", "Cointreau", "Malibu", "Midori",

    # RTD/Cider
    "Smirnoff Ice", "Cruiser", "Codys", "KGB", "Woodstock",
    "Somersby", "Rekorderlig", "Strongbow", "Old Mout", "Zeffer",
]

# Category keywords (ordered by specificity - more specific first)
CATEGORY_KEYWORDS = {
    # Spirits (specific types first)
    "vodka": ["vodka"],
    "gin": ["gin"],
    "rum": ["rum"],
    "whisky": ["whisky", "whiskey"],
    "bourbon": ["bourbon"],
    "scotch": ["scotch"],
    "tequila": ["tequila"],
    "brandy": ["brandy", "cognac"],
    "liqueur": ["liqueur", "schnapps", "amaretto", "baileys", "kahlua", "cointreau"],

    # Wine (specific types)
    "champagne": ["champagne", "moet", "veuve clicquot"],
    "sparkling": ["sparkling", "prosecco", "cava"],
    "red_wine": ["red wine", "shiraz", "merlot", "cabernet", "pinot noir"],
    "white_wine": ["white wine", "sauvignon blanc", "chardonnay", "pinot gris", "riesling"],
    "rose": ["rose", "rosé"],

    # Beer (specific types - order matters for specificity)
    "ipa": ["india pale ale", "ipa", "hazy ipa", "west coast ipa", "new england ipa", "neipa", "double ipa", "triple ipa"],
    "stout": ["stout", "porter", "imperial stout", "guinness"],
    "lager": ["lager", "pilsner", "pilsener"],
    "ale": ["pale ale", "amber ale", "brown ale", "golden ale", "session ale", "ale"],
    "craft_beer": ["craft beer"],

    # Broader categories
    "beer": ["beer"],
    "wine": ["wine"],
    "spirits": ["spirit"],
    "cider": ["cider"],
    "rtd": ["rtd", "ready to drink", "premix", "cruiser", "cody", "woodstock"],
    "mixer": ["tonic", "soda", "ginger ale", "cola"],
    "non_alcoholic": ["non-alcoholic", "alcohol free", "0%", "zero alcohol"],
}


def infer_brand(product_name: str) -> Optional[str]:
    """
    Infer brand from product name by matching against known brands.
    Returns the first matching brand found.
    """
    name_lower = product_name.lower()

    for brand in KNOWN_BRANDS:
        if brand.lower() in name_lower:
            return brand

    # If no known brand found, try to extract first word(s) before common separators
    # This catches brands we don't know about
    words = product_name.split()
    if words:
        # Return first 1-2 words as potential brand
        potential_brand = words[0]
        if len(words) > 1 and len(words[1]) > 2:
            # Include second word if it's not a common descriptor
            common_descriptors = ["red", "white", "dry", "sweet", "light", "dark", "premium"]
            if words[1].lower() not in common_descriptors:
                potential_brand = f"{words[0]} {words[1]}"
        return potential_brand

    return None


# Brand to category mapping for brands that don't always have category in name
BRAND_CATEGORY_MAP = {
    # Beer brands
    "heineken": "beer", "corona": "beer", "stella artois": "beer", "budweiser": "beer",
    "carlsberg": "beer", "guinness": "stout", "peroni": "beer", "asahi": "beer",
    "tui": "beer", "speight's": "beer", "steinlager": "beer", "lion red": "beer",
    "export gold": "beer", "db": "beer", "monteiths": "beer",

    # Wine brands
    "cloudy bay": "wine", "kim crawford": "wine", "oyster bay": "wine",
    "villa maria": "wine", "brancott": "wine", "matua": "wine",

    # Spirits brands
    "smirnoff": "vodka", "absolut": "vodka", "grey goose": "vodka",
    "gordon's": "gin", "bombay": "gin", "tanqueray": "gin",
    "bacardi": "rum", "captain morgan": "rum", "havana club": "rum",
    "jack daniel's": "whisky", "jim beam": "bourbon", "johnnie walker": "whisky",
    "jameson": "whisky", "chivas": "whisky",

    # RTD brands
    "cruiser": "rtd", "codys": "rtd", "woodstock": "rtd", "kgb": "rtd",

    # Cider brands
    "somersby": "cider", "strongbow": "cider", "rekorderlig": "cider",
    "old mout": "cider", "zeffer": "cider",
}


def infer_category(product_name: str) -> Optional[str]:
    """
    Infer product category from name by matching keywords.
    Returns the most specific category match (longest keyword match).
    """
    name_lower = product_name.lower()

    # First, try keyword-based matching (most specific)
    # This catches "India Pale Ale", "Sauvignon Blanc", etc.
    best_match = None
    best_match_length = 0

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name_lower and len(keyword) > best_match_length:
                best_match = category
                best_match_length = len(keyword)

    # If we found a specific keyword match (longer than 4 chars), use it
    # This prevents generic brand mappings from overriding specific types
    if best_match and best_match_length > 4:
        return best_match

    # Otherwise, check brand-specific mappings as fallback
    # Only use these for products without clear type indicators
    for brand, category in BRAND_CATEGORY_MAP.items():
        if brand in name_lower:
            return category

    # Return the keyword match even if it's short (e.g., "ale", "gin")
    return best_match


# Category hierarchy - maps specific categories to their parent categories
CATEGORY_HIERARCHY = {
    # Beer subcategories → beer
    "ipa": "beer",
    "stout": "beer",
    "lager": "beer",
    "ale": "beer",
    "craft_beer": "beer",

    # Wine subcategories → wine
    "white_wine": "wine",
    "red_wine": "wine",
    "rose": "wine",
    "sparkling": "wine",
    "champagne": "wine",

    # Spirits are already top-level (vodka, gin, rum, whisky, etc.)
    # But some have subcategories
    "bourbon": "whisky",
    "scotch": "whisky",
}


def get_parent_category(category: str) -> str | None:
    """
    Get the parent category for a given category.
    Returns None if the category is already a top-level category.
    """
    return CATEGORY_HIERARCHY.get(category)


def get_category_with_parent(category: str) -> tuple[str, str | None]:
    """
    Get both the specific category and its parent category.
    Returns (category, parent_category) tuple.
    """
    return (category, get_parent_category(category))


__all__ = [
    "parse_volume",
    "ParsedVolume",
    "extract_abv",
    "infer_brand",
    "infer_category",
    "get_parent_category",
    "get_category_with_parent",
    "CATEGORY_HIERARCHY",
]
