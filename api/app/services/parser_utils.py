from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

VOLUME_PATTERN = re.compile(
    r"(?P<count>\d+)\s*[x×]\s*(?P<unit>\d+(?:\.\d+)?)\s*(?P<measure>ml|l|ltr|litre|litres|liters)"
)
SINGLE_VOLUME_PATTERN = re.compile(
    r"(?P<unit>\d+(?:\.\d+)?)\s*(?P<measure>ml|l|ltr|litre|litres|liters)"
)
ABV_PATTERN = re.compile(r"(?P<abv>\d{1,2}(?:\.\d+)?)\s*%")


@dataclass(frozen=True)
class ParsedVolume:
    pack_count: Optional[int]
    unit_volume_ml: Optional[float]
    total_volume_ml: Optional[float]


def parse_volume(text: str) -> ParsedVolume:
    normalized = text.lower().replace("litre", "l").replace("litres", "l")
    normalized = normalized.replace("liters", "l").replace("ltr", "l")
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
    "tequila": ["tequila", "blanco", "reposado", "anejo", "añejo"],
    "brandy": ["brandy", "cognac"],
    "liqueur": ["liqueur", "schnapps", "amaretto", "baileys", "kahlua", "cointreau", "sambuca", "pimms", "ouzo", "jagermeister", "jägermeister", "limoncello", "amarula", "cream liqueur"],
    "soju": ["soju"],

    # Wine (specific types)
    "champagne": ["champagne", "moet", "veuve clicquot"],
    "sparkling": ["sparkling", "prosecco", "cava", "brut", "methode traditionnelle"],
    "fortified_wine": ["port", "tawny", "sherry", "vermouth", "marsala", "madeira"],
    "red_wine": ["red wine", "red blend", "shiraz", "syrah", "merlot", "cabernet", "cab sauv", "cab/sauv", "c/sauv", "cabernet sauvignon", "pinot noir", "tempranillo", "malbec", "bordeaux"],
    "white_wine": ["white wine", "sauvignon blanc", "sauv blanc", "sauvb", "chardonnay", "chard", "pinot gris", "pinot grigio", "pinot grigo", "riesling", "moscato"],
    "rose": ["rose", "rosé"],

    # Beer (specific types - order matters for specificity)
    "ipa": ["india pale ale", "ipa", "hazy ipa", "west coast ipa", "new england ipa", "neipa", "double ipa", "triple ipa"],
    "stout": ["stout", "porter", "imperial stout", "guinness"],
    "lager": ["lager", "pilsner", "pilsener", "pils"],
    "ale": ["pale ale", "amber ale", "brown ale", "golden ale", "session ale", "ale"],
    "craft_beer": ["craft beer"],

    # Broader categories
    "beer": ["beer"],
    "wine": ["wine"],
    "spirits": ["spirit"],
    "cider": ["cider"],
    "rtd": ["rtd", "ready to drink", "premix", "cruiser", "cody", "woodstock", "mule", "moscow mule", "g&t", "g & t", "gin & tonic", "vodka & ", "rum & "],
    "mixer": [
        "tonic", "tonic water", "soda", "soda water", "club soda",
        "ginger ale", "ginger beer", "dry ginger",
        "cola", "coke", "coca cola", "coca-cola", "pepsi",
        "sprite", "7up", "seven up", "fanta",
        "lemonade", "schweppes", "fever-tree", "fevertree",
        "bitters",
    ],
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
    "tui": "beer", "speight's": "beer", "speights": "beer", "steinlager": "beer", "lion red": "beer",
    "export gold": "beer", "export ultra": "beer", "export 33": "beer", "export": "beer",
    "db": "beer", "monteiths": "beer", "monteith's": "beer",
    "behemoth": "beer", "canyon": "beer", "garage project": "beer", "g/p": "beer", "parrotdog": "beer",
    "epic": "beer", "tuatara": "beer", "panhead": "beer", "emerson's": "beer", "emersons": "beer",
    "fosters": "beer", "foster's": "beer", "kingfisher": "beer",
    "tiger": "beer", "sapporo": "beer", "kirin": "beer",
    "victoria bitter": "beer", "waikato": "beer", "waikato draught": "beer",
    "pure blonde": "beer",
    "red horse": "beer", "chang": "beer", "wakachangi": "beer",
    "sawmill": "beer", "boundary road": "beer",
    "brb": "beer", "brb ultra": "beer",
    "little fat": "beer", "little number": "beer",

    # Wine brands
    "cloudy bay": "wine", "kim crawford": "wine", "oyster bay": "wine",
    "villa maria": "wine", "brancott": "wine", "matua": "wine",
    "cable bay": "wine", "coppola": "wine", "cleanskin": "wine",
    "wolf blass": "wine", "berton": "wine", "country dry": "wine",
    "brown brothers": "wine", "lindauer": "sparkling",
    "hawkes bay": "wine", "19 crimes": "wine",
    "mumm": "champagne", "chateau": "wine",

    # Spirits brands
    "smirnoff": "vodka", "absolut": "vodka", "grey goose": "vodka",
    "gordon's": "gin", "bombay": "gin", "tanqueray": "gin",
    "scapegrace": "gin",
    "bacardi": "rum", "captain morgan": "rum", "havana club": "rum", "malibu": "rum", "bumbu": "rum",
    "jack daniel's": "whisky", "jack daniels": "whisky", "gentleman jack": "whisky",
    "jim beam": "bourbon", "johnnie walker": "whisky",
    "jameson": "whisky", "chivas": "whisky", "canadian club": "whisky",
    "wild turkey": "bourbon", "old forester": "bourbon", "ole smoky": "whisky",
    "glenlivet": "whisky", "glenfiddich": "whisky", "j&b": "whisky",
    "el jimador": "tequila", "jose cuervo": "tequila", "olmeca": "tequila",
    "casamigos": "tequila", "casa noble": "tequila",
    "sourz": "liqueur", "galliano": "liqueur", "pimms": "liqueur",
    "de kuyper": "liqueur", "jagermeister": "liqueur",
    "midori": "liqueur", "pallini": "liqueur", "vok": "liqueur",
    "chasseur": "liqueur", "luxardo": "liqueur", "amarula": "liqueur",
    "saturdays": "liqueur",

    # RTD brands (specific product lines that are RTD, not their base spirits)
    "cruiser": "rtd", "codys": "rtd", "woodstock": "rtd", "kgb": "rtd",
    "hyoketsu": "rtd", "kedah": "rtd", "alba": "rtd", "royal dutch": "rtd", "grog": "rtd",
    "odd co": "rtd", "speights summit": "rtd",
    "long white": "rtd", "long": "rtd",  # "Long" alone often refers to Long White
    "hard rated": "rtd", "cheeky": "rtd", "batched": "rtd",
    "pals": "rtd", "nitro": "rtd", "white claw": "rtd",
    "clean collective": "rtd", "shots": "rtd",
    "buzzballz": "rtd", "nectar": "rtd", "alize": "rtd",
    "kings": "rtd", "haagen": "rtd",

    # Cider brands
    "somersby": "cider", "strongbow": "cider", "rekorderlig": "cider",
    "old mout": "cider", "zeffer": "cider",

    # Mixer brands
    "coca cola": "mixer", "coca-cola": "mixer", "coke": "mixer",
    "pepsi": "mixer", "sprite": "mixer", "7up": "mixer", "seven up": "mixer",
    "fanta": "mixer", "schweppes": "mixer", "fever-tree": "mixer", "fevertree": "mixer",
    "bundaberg": "mixer",

    # Additional brand fixes from data gaps
    "sheep dog": "whisky",
    "billy maverick": "bourbon",
    "bruichladdich": "scotch",
    "laphroaig": "scotch",
    "bowmore": "scotch",
    "dalmore": "scotch",
    "ballantine": "scotch",
    "bell's": "scotch",
    "woodford reserve": "bourbon",
    "finlandia": "vodka",
    "ciroc": "vodka",
    "greenall's": "gin",
    "greenall’s": "gin",
    "martell": "brandy",
    "st-remy": "brandy",
    "st-rémy": "brandy",
    "sailor jerry": "rum",
    "passion pop": "sparkling",
    "pasqua": "wine",
    "giesen": "wine",
    "hardy's": "wine",
    "hardys": "wine",
    "country medium": "wine",
    "sol": "beer",
    "speight gold": "beer",
    "fireball": "liqueur",
    "besos margarita": "rtd",
    "crimson badger": "beer",
    "ormond rich": "wine",
    "balvenie": "scotch",
    "talisker": "scotch",
    "cragganmore": "scotch",
    "dalwhinnie": "scotch",
    "benriach": "scotch",
    "tullamore": "whisky",
    "aperol": "liqueur",
    "bailey's": "liqueur",
    "baileys": "liqueur",
    "canterbury cream": "liqueur",
    "mount gay": "rum",
    "beefeater": "gin",
    "double brown": "beer",
    "stella": "beer",
    "flame": "beer",
    "purple goanna": "rtd",
    "pal's": "rtd",
    "pals": "rtd",
    "diesel": "rtd",
    "frankys lemon": "mixer",
    "gordon 4x6pk": "rtd",
    "tamnavulin": "scotch",
    "glenkinchie": "scotch",
    "imperial blue": "whisky",
    "antiquity blue": "whisky",
    "toki": "whisky",
    "sazerac rye": "whisky",
    "remy martin": "brandy",
    "rémy martin": "brandy",
    "pepe lopez": "tequila",
    "bacardi spiced": "rum",
    "bacardí spiced": "rum",
    "mount brewing": "beer",
    "fat bird": "cider",
    "mud shake": "rtd",
    "mudshake": "rtd",
    "pal’s": "rtd",
    "nola rich": "wine",
    "corte vigna": "wine",
    "velluto rosso": "wine",
    "taula big": "wine",
    "de valcourt": "wine",
    "1800": "tequila",
    "8pm": "whisky",
    "aberlour": "scotch",
    "auchentoshan": "scotch",
    "blenders pride": "whisky",
    "campari": "liqueur",
    "caol ila": "scotch",
    "country soft": "wine",
    "daniel le brun": "sparkling",
    "diplomatico": "rum",
    "diplomático": "rum",
    "drambuie": "liqueur",
    "early times": "bourbon",
    "estrella damm": "beer",
    "fiji gold": "beer",
    "glen grant": "scotch",
    "glenggrant": "scotch",
    "glenmorangie": "scotch",
    "godfather": "beer",
    "grant's": "whisky",
    "grants": "whisky",
    "great northern": "beer",
    "haymans": "gin",
    "hayman's": "gin",
    "highland park": "scotch",
    "jules taylor": "wine",
    "jura": "scotch",
    "kahlua": "liqueur",
    "kahlúa": "liqueur",
    "kilkenny": "beer",
    "king robert": "whisky",
    "lemsecco": "sparkling",
    "lion brown": "beer",
    "los siete": "tequila",
    "l&p": "mixer",
    "main divide": "wine",
    "nola's rich": "wine",
    "royal challenge": "whisky",
    "whyte": "whisky",
    "seagers lime": "rtd",
    "seager lime": "rtd",
    "daniel": "sparkling",
    "oban": "scotch",
    "mcguigan": "wine",
    "the balvenie": "scotch",
    "st-rã©my": "brandy",
    "st-rémy": "brandy",
    "nz pure": "vodka",
    "michelob": "beer",
    "quick brown": "beer",
    "matawhero": "wine",
    "veuve": "champagne",
    "trinity hill": "wine",
    "riccadonna": "sparkling",
    "signature": "whisky",
    "ranfurly draught": "beer",
    "taylors": "wine",
    "mud house": "wine",
    "nz liquor": "liqueur",
    "old crow": "bourbon",
    "o'mara's": "liqueur",
    "omaras": "liqueur",
    "paquera": "tequila",
    "peter lehmann": "wine",
    "teacher's": "whisky",
    "te mata": "wine",
    "the macallan": "scotch",
}


def infer_category(product_name: str) -> Optional[str]:
    """
    Infer product category from name by matching keywords.
    Returns the most specific category match (longest keyword match).
    """
    name_lower = product_name.lower()

    def has_alcohol_indicator(text: str) -> bool:
        return bool(
            ABV_PATTERN.search(text)
            or "alcoholic" in text
            or "alc" in text
            or "spiked" in text
            or "hard " in text
        )

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
        if best_match == "mixer" and has_alcohol_indicator(name_lower):
            return "rtd"
        return best_match

    # Mixer keywords with alcohol indicators should be RTDs, not mixers
    if best_match == "mixer" and has_alcohol_indicator(name_lower):
        return "rtd"

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
    "fortified_wine": "wine",

    # Spirits are already top-level (vodka, gin, rum, whisky, etc.)
    # But some have subcategories
    "bourbon": "whisky",
    "scotch": "whisky",
}


# NZ wine regions for deduplication
NZ_REGIONS = {
    "marlborough", "hawkes bay", "hawke's bay", "central otago", "gisborne",
    "wairarapa", "martinborough", "nelson", "canterbury", "waipara",
    "auckland", "northland", "waikato", "bay of plenty",
}

# Words that should stay lowercase in titles (unless first word)
LOWERCASE_WORDS = {"a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}

# Words that should stay uppercase
UPPERCASE_WORDS = {"ipa", "abv", "nz", "usa", "uk", "rtd", "ml", "cl", "xl"}


def format_product_name(name: str, brand: Optional[str] = None) -> str:
    """
    Format a product name for professional display.

    - Applies title case
    - Removes duplicate brand mentions
    - Removes duplicate region mentions
    - Cleans up whitespace

    Example: "stoneleigh marlborough stoneleigh sauvignon blanc marlborough"
          -> "Stoneleigh Sauvignon Blanc Marlborough"
    """
    if not name:
        return name

    # Normalize whitespace
    words = name.lower().split()
    if not words:
        return name

    # Track seen words for deduplication (case-insensitive)
    seen_words: set[str] = set()
    seen_regions: set[str] = set()
    result_words: list[str] = []

    # Determine brand words to deduplicate
    brand_words: set[str] = set()
    if brand:
        brand_words = {w.lower() for w in brand.split()}

    i = 0
    while i < len(words):
        word = words[i]
        word_lower = word.lower()

        # Check for multi-word regions (e.g., "hawkes bay", "central otago")
        two_word = f"{word_lower} {words[i+1].lower()}" if i + 1 < len(words) else None

        if two_word and two_word in NZ_REGIONS:
            if two_word not in seen_regions:
                seen_regions.add(two_word)
                # Title case the region
                result_words.append(words[i].capitalize())
                result_words.append(words[i+1].capitalize())
            i += 2
            continue

        # Check for single-word regions
        if word_lower in NZ_REGIONS:
            if word_lower not in seen_regions:
                seen_regions.add(word_lower)
                result_words.append(word.capitalize())
            i += 1
            continue

        # Skip duplicate brand words (but keep first occurrence)
        if word_lower in brand_words:
            if word_lower not in seen_words:
                seen_words.add(word_lower)
                result_words.append(_title_case_word(word))
            i += 1
            continue

        # Skip exact duplicate words in sequence
        if word_lower in seen_words and word_lower not in LOWERCASE_WORDS:
            i += 1
            continue

        seen_words.add(word_lower)
        result_words.append(_title_case_word(word))
        i += 1

    # Apply proper title case rules
    formatted = []
    for idx, word in enumerate(result_words):
        if idx == 0:
            # First word always capitalized
            formatted.append(word if word.upper() in {w.upper() for w in UPPERCASE_WORDS} else word.capitalize() if word.islower() else word)
        elif word.lower() in LOWERCASE_WORDS:
            formatted.append(word.lower())
        else:
            formatted.append(word)

    return " ".join(formatted)


def _title_case_word(word: str) -> str:
    """Apply title case to a single word, respecting special cases."""
    word_lower = word.lower()

    # Keep certain words uppercase
    if word_lower in UPPERCASE_WORDS:
        return word.upper()

    # Handle apostrophes (e.g., "hawke's" -> "Hawke's")
    if "'" in word:
        parts = word.split("'")
        return "'".join(p.capitalize() for p in parts)

    # Standard title case
    return word.capitalize()


__all__ = [
    "parse_volume",
    "ParsedVolume",
    "extract_abv",
    "infer_brand",
    "infer_category",
    "CATEGORY_HIERARCHY",
    "format_product_name",
]
