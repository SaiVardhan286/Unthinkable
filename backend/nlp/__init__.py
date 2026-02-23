"""
NLP package for the Voice Command Shopping Assistant.

This module exposes a small, stable facade of pure functions that can be
imported directly in application code and tests.
"""
from __future__ import annotations

from .categories import categorize_item
from .filters import extract_filters
from .intent import detect_intent
from .language import detect_language
from .parser import extract_item, parse_voice_command
from .quantity import extract_quantity

__all__ = [
    "detect_language",
    "detect_intent",
    "extract_quantity",
    "extract_filters",
    "categorize_item",
    "extract_item",
    "parse_voice_command",
]

