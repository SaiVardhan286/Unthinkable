from __future__ import annotations

CATEGORY_KEYWORDS = {
    "dairy": {"milk", "cheese", "yogurt", "butter"},
    "produce": {"apple", "apples", "banana", "bananas", "lettuce", "tomato", "tomatoes", "onion", "onions"},
    "snacks": {"chips", "cookies", "crackers", "granola"},
    "beverages": {"water", "juice", "soda", "coffee", "tea"},
    "bakery": {"bread", "bagel", "croissant"},
    "pantry": {"rice", "pasta", "beans", "flour", "sugar", "salt"},
}


def categorize_item(item: str) -> str:
    """
    Map an item name to a high-level category.
    """
    if not item:
        return "other"
    item_l = item.lower()
    for cat, words in CATEGORY_KEYWORDS.items():
        if any(w in item_l for w in words):
            return cat
    return "other"

