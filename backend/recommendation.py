from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from config import get_settings
from models import UserHistory, ShoppingItem
from schemas import SuggestionGroup


SUBSTITUTE_MAP: dict[str, list[str]] = {
    "milk": ["almond milk", "soy milk", "oat milk"],
    "sugar": ["brown sugar", "stevia"],
    "butter": ["olive oil", "ghee", "margarine"],
    "eggs": ["flax eggs", "chia eggs"],
    "chips": ["popcorn", "pretzels"],
}


def seasonal_items_for_month(month: int) -> list[str]:
    # Simple demo logic using broad seasons.
    if month in {6, 7, 8}:  # Summer
        return ["watermelon", "mango", "cold drinks"]
    if month in {12, 1, 2}:  # Winter
        return ["soup", "oranges"]
    if month in {3, 4, 5}:  # Spring
        return ["strawberries", "asparagus", "spinach"]
    # Autumn / fallback
    return ["pumpkin", "apples", "cinnamon"]


def _dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        k = x.strip().lower()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(x)
    return out


@dataclass
class RecommendationService:
    db: Session
    history_min_purchases: int
    history_limit: int

    @classmethod
    def from_session(cls, db: Session) -> "RecommendationService":
        settings = get_settings()
        return cls(
            db=db,
            history_min_purchases=settings.history_min_purchases,
            history_limit=settings.history_suggestion_limit,
        )

    def get_history_based(self) -> list[str]:
        """
        Get top recommendations based on user history.
        Score = purchase_count * 2 + search_count
        Only include items with total interactions >= 2
        Return top 3 items sorted by score
        """
        
        q = (
            select(UserHistory)
            .where(
                (UserHistory.purchase_count + UserHistory.search_count) >= 2
            )
            .order_by(
                desc(
                    UserHistory.purchase_count * 2 + UserHistory.search_count
                )
            )
            .limit(3)
        )
        rows = self.db.execute(q).scalars().all()
        return [r.item_name for r in rows]

    def get_seasonal(self) -> list[str]:
        return seasonal_items_for_month(datetime.utcnow().month)

    def get_substitutes_for_items(self, current_items: Iterable[ShoppingItem], limit: int = 5) -> list[str]:
        base = [i.name.lower() for i in current_items]
        suggestions: list[str] = []
        for name in base:
            for k, subs in SUBSTITUTE_MAP.items():
                if k in name:
                    suggestions.extend(subs)
        return _dedupe_preserve_order(suggestions)[:limit]

    def get_substitutes_for_query(self, query: str, limit: int = 5) -> list[str]:
        """
        Suggest substitutes when a searched item is unavailable.
        """
        q = query.lower().strip()
        suggestions: list[str] = []
        for key, subs in SUBSTITUTE_MAP.items():
            if key in q:
                suggestions.extend(subs)
        return _dedupe_preserve_order(suggestions)[:limit]

    def get_combined_suggestions(self, current_items: list[ShoppingItem]) -> SuggestionGroup:
        previous = self.get_history_based()
        seasonal = self.get_seasonal()
        substitutes = self.get_substitutes_for_items(current_items, limit=5)

        all_s = _dedupe_preserve_order([*previous, *seasonal, *substitutes])
        return SuggestionGroup(previous=previous, seasonal=seasonal, substitutes=substitutes, all=all_s)


def build_suggestions(db: Session, current_items: list[ShoppingItem]) -> SuggestionGroup:
    """
    Backwards-compatible helper used by existing code.
    """
    service = RecommendationService.from_session(db)
    return service.get_combined_suggestions(current_items)


