from __future__ import annotations

import logging
import re

logger = logging.getLogger("nlp.quantity")


NUMBER_WORDS_EN = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

NUMBER_WORDS_ES = {
    "uno": 1,
    "una": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
}


def extract_quantity(text: str, language: str) -> int:
    """
    Extract a positive integer quantity from text, remove matched quantity words, and return cleaned_text.
    Supports number words (one, two, three, etc.).
    Returns (quantity, cleaned_text).
    """
    t = text.lower()
    quantity = 1
    cleaned_text = t

    # Prefer explicit digits.
    m = re.search(r"\b(\d+)\b", t)
    if m:
        try:
            q = int(m.group(1))
            if q > 0:
                quantity = q
                cleaned_text = re.sub(r"\b" + re.escape(m.group(1)) + r"\b", " ", cleaned_text)
        except ValueError:
            logger.warning("Failed to parse integer quantity from %s", m.group(1))

    # Fallback to number words.
    words = NUMBER_WORDS_ES if language == "es" else NUMBER_WORDS_EN
    for w, v in words.items():
        if re.search(rf"\b{re.escape(w)}\b", cleaned_text):
            quantity = v
            cleaned_text = re.sub(rf"\b{re.escape(w)}\b", " ", cleaned_text)
            break

    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
    return quantity, cleaned_text

