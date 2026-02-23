from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from nlp.fuzzy import fuzzy_match_item
from schemas import Filters

logger = logging.getLogger("search_service")

MOCK_PRODUCTS_PATH = Path(__file__).parent / "mock_products.json"


class SearchService:
    """
    Search products from mock_products.json with support for filters:
    - Brand filtering
    - Size filtering
    - Price range filtering
    - Fuzzy name matching
    """

    def __init__(self):
        self.products = self.load_products()

    def load_products(self) -> list[dict[str, Any]]:
        """Load products from mock_products.json."""
        try:
            with open(MOCK_PRODUCTS_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.exception("Failed to load products")
            return []

    def filter_by_name(self, items: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
        if not query:
            return items
        query_lower = query.lower()
        return [p for p in items if query_lower in p.get("name", "").lower()]

    def filter_by_brand(self, items: list[dict[str, Any]], brand: str) -> list[dict[str, Any]]:
        if not brand:
            return items
        brand_lower = brand.lower()
        return [p for p in items if brand_lower in p.get("brand", "").lower()]

    def filter_by_size(self, items: list[dict[str, Any]], size: str) -> list[dict[str, Any]]:
        if not size:
            return items
        size_lower = size.lower()
        return [p for p in items if size_lower in p.get("size", "").lower()]

    def filter_by_price(self, items: list[dict[str, Any]], price_max: float) -> list[dict[str, Any]]:
        if price_max <= 0:
            return items
        return [p for p in items if p.get("price", 0) <= price_max]

    def apply_fuzzy_match(self, items: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
        if not query or not items:
            return []
        query_lower = query.lower()
        product_names = [p.get("name", "") for p in items]
        fuzzy_matches = fuzzy_match_item(query_lower, product_names, cutoff=0.5)
        if fuzzy_matches:
            return [p for p in items if p.get("name", "") in fuzzy_matches]
        return []

    def search(self, query: str, filters: Filters) -> list[dict[str, Any]]:
        """
        Search products by query and filters using pipeline execution.
        """
        results = self.products[:]

        # 1. Match by item name
        name_matches = self.filter_by_name(results, query)
        
        # 5. If empty -> fuzzy match fallback (before strong filters)
        if not name_matches and query:
            name_matches = self.apply_fuzzy_match(results, query)

        results = name_matches if name_matches else results

        # 2. Filter by brand
        results = self.filter_by_brand(results, filters.brand)

        # 3. Filter by size
        results = self.filter_by_size(results, filters.size)

        # 4. Filter by price
        results = self.filter_by_price(results, filters.price_max)

        return results
