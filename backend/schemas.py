from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


Action = Literal["add", "remove", "modify", "search", "invalid"]


class Filters(BaseModel):
    brand: str = ""
    price_max: float = 0
    size: str = ""


class ParsedVoiceCommand(BaseModel):
    action: Action
    item: str = ""
    quantity: int = 1
    category: str = "other"
    filters: Filters = Field(default_factory=Filters)
    language: str = "en"
    raw_text: str


class VoiceRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    language: Optional[str] = Field(default=None, description="Optional BCP-47 hint: en, es, ...")


class ModifyItemRequest(BaseModel):
    item: str = Field(min_length=1, max_length=120)
    quantity: int = Field(ge=1, le=100, description="New quantity (1-100). If 0, item is deleted.")



class ShoppingItemOut(BaseModel):
    id: int
    name: str
    quantity: int
    category: str
    brand: str = ""
    price: float = 0.0
    size: str = ""

    class Config:
        from_attributes = True


class SuggestionGroup(BaseModel):
    previous: list[str] = Field(default_factory=list)
    seasonal: list[str] = Field(default_factory=list)
    substitutes: list[str] = Field(default_factory=list)
    all: list[str] = Field(default_factory=list)


class ProcessVoiceResponse(BaseModel):
    parsed: ParsedVoiceCommand
    items: list[ShoppingItemOut]
    suggestions: SuggestionGroup
    search_results: list[dict[str, Any]] = Field(default_factory=list)

    # Convenience mirrors for API consumers; keeps old shape but surfaces
    # the most important fields at the top level.
    action: str | None = None
    item: str | None = None
    quantity: int | None = None
    category: str | None = None
    suggestions_flat: list[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query_text: str = ""
    voice_text: str = ""
    brand: str = ""
    price_max: float = 0


class SearchResponse(BaseModel):
    query: str
    filters: Filters
    results: list[dict[str, Any]]

