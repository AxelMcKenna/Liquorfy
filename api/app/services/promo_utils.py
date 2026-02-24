"""Utilities for parsing promotional pricing and deal information."""
from __future__ import annotations

import re
from datetime import datetime, time
from typing import Optional

import pytz

# NZ timezone for date parsing
NZ_TZ = pytz.timezone("Pacific/Auckland")

# Member-only keywords (case-insensitive)
MEMBER_KEYWORDS = [
    "club",
    "clubcard",
    "member",
    "members",
    "onecard",
    "loyalty",
    "rewards",
]

# Pre-compiled word-boundary patterns for member-only detection
_MEMBER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
    for kw in MEMBER_KEYWORDS
]


def parse_promo_price(text: str) -> Optional[float]:
    """
    Extract numeric price from promotional text.

    Args:
        text: Text containing price (e.g., "$19.99", "Save $5.00", "3 for $50")

    Returns:
        Float price or None if no price found

    Examples:
        >>> parse_promo_price("$19.99")
        19.99
        >>> parse_promo_price("Save $5.00")
        5.0
        >>> parse_promo_price("3 for $50.00")
        50.0
    """
    if not text:
        return None

    # Remove commas from numbers
    text = text.replace(",", "")

    # Match price patterns: $19.99, 19.99, etc.
    price_pattern = r'\$?\s*([\d]+\.?\d*)'
    match = re.search(price_pattern, text)

    if match:
        try:
            return float(match.group(1))
        except (ValueError, AttributeError):
            return None

    return None


def parse_multi_buy_deal(text: str) -> Optional[dict]:
    """
    Parse multi-buy promotional deals.

    Args:
        text: Deal text (e.g., "3 for $50", "2 for 1", "Buy 2 Get 1 Free")

    Returns:
        Dict with quantity, total_price, unit_price, deal_text or None

    Examples:
        >>> parse_multi_buy_deal("3 for $50")
        {"quantity": 3, "total_price": 50.0, "unit_price": 16.67, "deal_text": "3 for $50"}
        >>> parse_multi_buy_deal("2 for 1")
        {"quantity": 2, "total_price": None, "unit_price": None, "deal_text": "2 for 1"}
    """
    if not text:
        return None

    text_lower = text.lower()

    # Pattern: "3 for $50", "3 for 50", "3for$50"
    pattern1 = r'(\d+)\s*for\s*\$?\s*([\d]+\.?\d*)'
    match1 = re.search(pattern1, text_lower)

    if match1:
        quantity = int(match1.group(1))
        total_price = float(match1.group(2))
        unit_price = round(total_price / quantity, 2)

        return {
            "quantity": quantity,
            "total_price": total_price,
            "unit_price": unit_price,
            "deal_text": text.strip(),
        }

    # Pattern: "2 for 1", "3 for 2"
    pattern2 = r'(\d+)\s*for\s*(\d+)'
    match2 = re.search(pattern2, text_lower)

    if match2:
        quantity_buy = int(match2.group(1))
        quantity_pay = int(match2.group(2))

        # Can't calculate exact unit price without knowing base price
        # But we can indicate it's a discount
        return {
            "quantity": quantity_buy,
            "total_price": None,
            "unit_price": None,  # Would need regular price to calculate
            "deal_text": text.strip(),
        }

    # Pattern: "Buy 2 Get 1 Free", "Buy 3 Get 1"
    pattern3 = r'buy\s*(\d+)\s*get\s*(\d+)(?:\s*free)?'
    match3 = re.search(pattern3, text_lower)

    if match3:
        buy_qty = int(match3.group(1))
        get_qty = int(match3.group(2))
        total_qty = buy_qty + get_qty

        return {
            "quantity": total_qty,
            "total_price": None,
            "unit_price": None,  # Would need regular price to calculate
            "deal_text": text.strip(),
        }

    return None


def parse_promo_end_date(text: str) -> Optional[datetime]:
    """
    Parse promotion end date from text.

    Args:
        text: Text containing date (e.g., "Ends 25/12/2024", "Until 25 Dec")

    Returns:
        Datetime object in NZ timezone or None

    Examples:
        >>> parse_promo_end_date("Ends 25/12/2024")
        datetime(2024, 12, 25, 23, 59, 59, tzinfo=NZ_TZ)
        >>> parse_promo_end_date("Until 25 Dec")
        datetime(2024, 12, 25, 23, 59, 59, tzinfo=NZ_TZ)
    """
    if not text:
        return None

    try:
        from dateutil import parser as date_parser
    except ImportError:
        # Fallback if dateutil not installed yet
        return None

    # Common NZ date patterns
    # DD/MM/YYYY, DD/MM/YY
    pattern1 = r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})'
    match1 = re.search(pattern1, text)

    if match1:
        day = int(match1.group(1))
        month = int(match1.group(2))
        year = int(match1.group(3))

        # Handle 2-digit years
        if year < 100:
            year += 2000

        try:
            # End of day for end dates
            dt = datetime(year, month, day, 23, 59, 59)
            return NZ_TZ.localize(dt)
        except ValueError:
            pass

    # Try to extract just the date part for flexible parsing
    # Look for patterns like "Ends 25 Dec", "Until Monday 25/12", etc.
    date_keywords = ['end', 'until', 'expires', 'valid', 'offer']

    for keyword in date_keywords:
        if keyword in text.lower():
            # Extract text after the keyword
            parts = text.lower().split(keyword)
            if len(parts) > 1:
                date_text = parts[1].strip()

                try:
                    # Use dateutil's flexible parser
                    # dayfirst=True for NZ date format (DD/MM not MM/DD)
                    dt = date_parser.parse(date_text, dayfirst=True, fuzzy=True)

                    # Set to end of day
                    dt = dt.replace(hour=23, minute=59, second=59)

                    # Add NZ timezone if naive
                    if dt.tzinfo is None:
                        dt = NZ_TZ.localize(dt)

                    return dt
                except (ValueError, TypeError):
                    continue

    # Last attempt: Try parsing the whole text
    try:
        dt = date_parser.parse(text, dayfirst=True, fuzzy=True)
        dt = dt.replace(hour=23, minute=59, second=59)

        if dt.tzinfo is None:
            dt = NZ_TZ.localize(dt)

        return dt
    except (ValueError, TypeError):
        return None


def detect_member_only(text: str) -> bool:
    """
    Detect if promotion is member-only.

    Args:
        text: Promotional text

    Returns:
        True if member-only keywords found

    Examples:
        >>> detect_member_only("Clubcard Price $19.99")
        True
        >>> detect_member_only("Member Only Deal")
        True
        >>> detect_member_only("Special Price $19.99")
        False
    """
    if not text:
        return False

    return any(pattern.search(text) for pattern in _MEMBER_PATTERNS)


def extract_promo_badge_text(node, selectors: list[str]) -> Optional[str]:
    """
    Extract promotional badge text from HTML node using multiple selectors.

    Args:
        node: HTML node (from selectolax or similar)
        selectors: List of CSS selectors to try in order

    Returns:
        Badge text or None

    Examples:
        >>> extract_promo_badge_text(node, ['.badge', '.promo', '[class*="special"]'])
        "3 for $50"
    """
    if not node or not selectors:
        return None

    for selector in selectors:
        try:
            badge = node.css_first(selector)
            if badge:
                text = badge.text(strip=True) if hasattr(badge, 'text') else badge.text_content.strip()
                if text:
                    return text
        except (AttributeError, Exception):
            continue

    return None


def extract_promo_info(
    node,
    promo_selectors: Optional[list[str]] = None,
    was_price_selectors: Optional[list[str]] = None,
    current_price: Optional[float] = None
) -> dict:
    """
    Extract comprehensive promotional information from HTML node.

    Args:
        node: HTML node (from selectolax)
        promo_selectors: CSS selectors for promo price elements
        was_price_selectors: CSS selectors for was-price elements
        current_price: Current price (used to detect was-price promos)

    Returns:
        Dict with keys: promo_price, promo_text, promo_ends_at, is_member_only

    Examples:
        >>> info = extract_promo_info(card, current_price=25.99)
        >>> info['promo_price']
        19.99
        >>> info['is_member_only']
        True
    """
    if promo_selectors is None:
        promo_selectors = [
            '[data-testid="product-promo-price"]',
            '[data-testid="product-badge"]',
            '[class*="promo"]',
            '[class*="special"]',
            '[class*="clubcard"]',
            '[class*="deal"]',
            '[class*="save"]',
            '.sale-price',
            '.promo-price',
            '.special-price',
        ]

    if was_price_selectors is None:
        was_price_selectors = [
            '[data-testid="product-was-price"]',
            '[class*="was-price"]',
            '[class*="old-price"]',
            '[class*="strikethrough"]',
            '.was-price',
            '.original-price',
            '.old-price',
        ]

    result = {
        "promo_price": None,
        "promo_text": None,
        "promo_ends_at": None,
        "is_member_only": False,
    }

    # Try to find promo element
    promo_elem = None
    for selector in promo_selectors:
        try:
            promo_elem = node.css_first(selector)
            if promo_elem:
                break
        except (AttributeError, Exception):
            continue

    if promo_elem:
        # Get raw text from promo element
        try:
            promo_raw_text = promo_elem.text(strip=True) if hasattr(promo_elem, 'text') else promo_elem.text_content.strip()
        except (AttributeError, Exception):
            promo_raw_text = None

        if promo_raw_text:
            # Extract price
            extracted_price = parse_promo_price(promo_raw_text)

            # Check for multi-buy deals
            multi_buy = parse_multi_buy_deal(promo_raw_text)
            if multi_buy:
                result["promo_text"] = multi_buy["deal_text"]
                if multi_buy.get("unit_price"):
                    result["promo_price"] = multi_buy["unit_price"]
                elif extracted_price:
                    result["promo_price"] = extracted_price
            else:
                result["promo_text"] = promo_raw_text[:255]
                if extracted_price:
                    # Only use extracted price if it's less than current price
                    if current_price is None or extracted_price < current_price:
                        result["promo_price"] = extracted_price

            # Parse end date
            result["promo_ends_at"] = parse_promo_end_date(promo_raw_text)

            # Detect member-only
            result["is_member_only"] = detect_member_only(promo_raw_text)

    # Check for was-price if no promo found yet
    if result["promo_price"] is None and current_price is not None:
        for selector in was_price_selectors:
            try:
                was_elem = node.css_first(selector)
                if was_elem:
                    was_text = was_elem.text(strip=True) if hasattr(was_elem, 'text') else was_elem.text_content.strip()
                    if was_text:
                        was_price = parse_promo_price(was_text)
                        if was_price and was_price > current_price:
                            # Current price is lower than was-price, so it's a promo
                            result["promo_price"] = current_price
                            result["promo_text"] = f"Was ${was_price:.2f}"[:255]
                            break
            except (AttributeError, Exception):
                continue

    return result


__all__ = [
    "parse_promo_price",
    "parse_multi_buy_deal",
    "parse_promo_end_date",
    "detect_member_only",
    "extract_promo_badge_text",
    "extract_promo_info",
]
