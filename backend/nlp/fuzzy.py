import difflib
import json
from pathlib import Path

MOCK_PRODUCTS_PATH = Path(__file__).parent.parent / "mock_products.json"

# Load product names from mock_products.json
with open(MOCK_PRODUCTS_PATH, encoding="utf-8") as f:
    PRODUCTS = [item["name"].lower() for item in json.load(f)]

def fuzzy_match_item(query: str, known_items: list[str] = None, cutoff: float = 0.7) -> list[str]:
    """
    Suggest closest item(s) from known items using difflib.
    """
    if known_items is None:
        known_items = PRODUCTS
    query = query.lower().strip()
    matches = difflib.get_close_matches(query, known_items, n=3, cutoff=cutoff)
    return matches
