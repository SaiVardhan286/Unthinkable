from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger("nlp.language")


def detect_language(text: str, hint: Optional[str] = None) -> str:
    """
    Detect language for the incoming text.

    Returns a short language code: "en" or "es".
    Falls back to "en" on ambiguity.
    """
    if hint:
        lowered = hint.lower()
        if lowered.startswith("es"):
            return "es"
        if lowered.startswith("en"):
            return "en"

    t = text.lower()

    # Quick heuristic: accented characters strongly suggest Spanish.
    if any(ch in t for ch in ("á", "é", "í", "ó", "ú", "ñ")):
        logger.debug("Detected Spanish via diacritics")
        return "es"

    if re.search(r"\b(necesito|agrega|añade|anade|busca|quita|borra|elimina)\b", t):
        logger.debug("Detected Spanish via keywords")
        return "es"

    logger.debug("Falling back to English language detection")
    return "en"

