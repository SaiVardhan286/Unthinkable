from __future__ import annotations

import logging
import re

from schemas import Filters

logger = logging.getLogger("nlp.filters")

SIZE_KEYWORDS = {
    "small": "small",
    "pequeño": "small",
    "chico": "small",
    "medium": "medium",
    "mediano": "medium",
    "large": "large",
    "grande": "large",
    "500ml": "500ml",
    "1l": "1L",
    "1 l": "1L",
    "2kg": "2kg",
    "2 kg": "2kg",
    "1kg": "1kg",
}


def _extract_price_max(text: str) -> float:
    t = text.lower()
    m = re.search(r"(?:under|below|less than|cheaper than|<=).*?(\d+(?:\.\d+)?)", t, flags=re.IGNORECASE)
    if not m:
        m = re.search(r"(?:menor que|bajo|menos de|por debajo de|hasta|<=).*?(\d+(?:\.\d+)?)", t, flags=re.IGNORECASE)
    if not m:
        return 0.0
    try:
        return float(m.group(1))
    except ValueError:  # pragma: no cover - defensive
        logger.warning("Failed to parse price_max from %s", m.group(1))
        return 0.0


def _extract_brand(text: str) -> str:
    t = text.lower()
    
    # Static fallback
    m = re.search(r"\b(?:brand|from|marca|de)\s+([a-zA-Z0-9][\w\-]+)", t, flags=re.IGNORECASE)
    brand_found = m.group(1) if m else ""

    # Dynamic extraction from mock_products
    try:
        import json
        from pathlib import Path
        path = Path(__file__).parent.parent / "mock_products.json"
        with path.open("r", encoding="utf-8") as f:
            products = json.load(f)
            brands = {p.get("brand", "").lower() for p in products if p.get("brand")}
            for b in brands:
                # check if brand appears as whole word in text
                if re.search(rf"\b{re.escape(b)}\b", t):
                    return b.title() # Return the capitalized version as we matched dynamically 
    except Exception as e:
        logger.warning(f"Failed to dynamically load brands: {e}")

    return brand_found.title() if brand_found else ""


def _extract_size(text: str) -> str:
    """
    Extract size descriptor from text.
    Supports: small, medium, large, 500ml, 1L, 2kg, etc.
    """
    t = text.lower()
    for keyword, size_value in SIZE_KEYWORDS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", t):
            return size_value
            
    # Also support trailing generic sizes in regex: "\d+(?:ml|l|kg|g|oz|lb)"
    m = re.search(r"\b(\d+(?:\.\d+)?\s*(?:ml|l|kg|g|oz|lb))\b", t)
    if m:
        return m.group(1).replace(" ", "")
        
    return ""


def extract_filters(text: str) -> Filters:
    """
    Extract brand / size / price filters from text.
    """
    brand = _extract_brand(text)
    size = _extract_size(text)
    price_max = _extract_price_max(text)
    return Filters(brand=brand, size=size, price_max=price_max)

