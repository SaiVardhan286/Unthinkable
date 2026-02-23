from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger("nlp.intent")


@dataclass(frozen=True)
class ActionLexicon:
    add: tuple[str, ...]
    remove: tuple[str, ...]
    modify: tuple[str, ...]
    search: tuple[str, ...]


LEXICON_EN = ActionLexicon(
    add=("add", "need", "buy", "get", "grab", "pick up"),
    remove=("remove", "delete", "drop", "take off", "clear"),
    modify=("change", "modify", "update", "set"),
    search=("search", "find", "look for", "show"),
)

LEXICON_ES = ActionLexicon(
    add=("agrega", "añade", "anade", "necesito", "compra", "comprar", "quiero"),
    remove=("elimina", "borra", "quita", "remueve"),
    modify=("cambia", "modifica", "actualiza", "pon", "establece", "ajusta"),
    search=("busca", "encuentra", "buscar", "muestra"),
)


def _has_any(text: str, words: tuple[str, ...]) -> bool:
    return any(re.search(rf"\b{re.escape(w)}\b", text) for w in words)


def _is_negated_add(text: str, language: str) -> bool:
    """
    Very small safety net for negations like "don't add milk" / "no agregues leche".
    In those cases we treat the command as non-mutating (search intent) so that
    the backend does not change the list.
    """
    if language == "es":
        return bool(re.search(r"\bno\s+agregues?\b", text))
    # English
    return bool(re.search(r"\b(do\s*not|don't|dont)\s+add\b", text))


def detect_intent(text: str, language: str) -> str:
    """
    Map free-form text into one of: add, remove, modify, search.
    """
    t = text.lower().strip()
    lex = LEXICON_ES if language == "es" else LEXICON_EN

    # Stop phrase detection
    stop_phrases = ["how", "why", "what", "make", "recipe"]
    if any(phrase in t for phrase in stop_phrases):
        return "invalid"

    if _is_negated_add(t, language):
        logger.debug("Detected negated add; downgrading to search intent")
        return "search"

    if _has_any(t, lex.search):
        return "search"
    if _has_any(t, lex.remove):
        return "remove"
    if _has_any(t, lex.modify):
        return "modify"

    # Only allow ADD if add keywords or pattern: quantity + noun
    add_keywords = lex.add
    has_add_kw = _has_any(t, add_keywords)
    # Pattern: quantity + noun (e.g., "two apples")
    quantity_noun_pattern = re.compile(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\b\s+\w+")
    has_quantity_noun = bool(quantity_noun_pattern.search(t))

    if has_add_kw or has_quantity_noun:
        return "add"

    # If nothing matches, treat as invalid
    return "invalid"

