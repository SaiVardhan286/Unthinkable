from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional

from pydantic import ValidationError

from nlp.categories import categorize_item
from nlp.filters import extract_filters
from nlp.intent import detect_intent
from nlp.language import detect_language
from nlp.quantity import extract_quantity
from schemas import Filters, ParsedVoiceCommand

logger = logging.getLogger("nlp.parser")


def extract_item(text: str, language: str) -> str:
    """
    Extract the item phrase from free text, stripping actions, quantities and
    container words while keeping the meaningful noun phrase.
    """
    t = re.sub(r"[^a-zA-Z0-9áéíóúñÁÉÍÓÚÑ\s\-]", " ", text).lower()
    t = re.sub(r"\s+", " ", t).strip()

    # Remove explicit quantities.
    t = re.sub(r"\b\d+\b", " ", t).strip()

    # Remove container words (bottle, pack, etc.) but keep the product.
    t = re.sub(r"\b(bottle|bottles|pack|packs|bag|bags|box|boxes|cans|can)\b", " ", t).strip()
    t = re.sub(r"\b(botella|botellas|paquete|paquetes|bolsa|bolsas|caja|cajas|latas|lata)\b", " ", t).strip()

    t = re.sub(r"\b(of|de)\b", " ", t).strip()

    # Remove common action/stop words.

    stopwords_en = {
        "a",
        "an",
        "the",
        "some",
        "of",
        "to",
        "for",
        "please",
        "me",
        "i",
        "we",
        "need",
        "want",
        "buy",
        "add",
        "remove",
        "delete",
        "change",
        "set",
        "update",
        "modify",
        "search",
        "find",
        "look",
        "show",
        "get",
    }

    stopwords_es = {
        "un",
        "una",
        "unos",
        "unas",
        "el",
        "la",
        "los",
        "las",
        "de",
        "del",
        "por",
        "para",
        "porfavor",
        "por",
        "favor",
        "yo",
        "necesito",
        "quiero",
        "compra",
        "agrega",
        "añade",
        "anade",
        "quita",
        "borra",
        "elimina",
        "cambia",
        "modifica",
        "actualiza",
        "busca",
        "muestra",
    }

    stop = stopwords_es if language == "es" else stopwords_en

    tokens = [tok for tok in t.split(" ") if tok and tok not in stop]
    return " ".join(tokens).strip()


def _openai_parse(text: str, language: str) -> Optional[ParsedVoiceCommand]:
    """
    Optional higher-quality parsing via OpenAI when configured.
    """
    if not os.getenv("OPENAI_API_KEY"):
        return None
    if os.getenv("ENABLE_OPENAI_PARSER", "false").lower() not in {"1", "true", "yes"}:
        return None

    try:
        from openai import OpenAI  # type: ignore
    except Exception:
        logger.exception("Failed to import OpenAI client; falling back to rule-based NLP")
        return None

    client = OpenAI()
    system = (
        "You extract structured shopping commands from voice text. "
        "Return ONLY valid JSON matching this schema:\n"
        '{ "action": "add/remove/modify/search", "item": "string", "quantity": int, '
        '"category": "string", "filters": { "brand": "", "price_max": 0 } }'
    )
    user = f"Language hint: {language}\nVoice text: {text}"

    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0,
    )
    raw = (resp.choices[0].message.content or "").strip()

    # Some models wrap JSON in fences; strip them.
    raw = re.sub(r"^```json\s*", "", raw, flags=re.IGNORECASE).strip()
    raw = re.sub(r"^```\s*", "", raw).strip()
    raw = re.sub(r"\s*```$", "", raw).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.exception("Failed to decode OpenAI JSON response")
        return None

    data["language"] = language
    data["raw_text"] = text
    try:
        return ParsedVoiceCommand.model_validate(data)
    except ValidationError:
        logger.exception("OpenAI parser returned invalid schema")
        return None


def parse_voice_command(text: str, language_hint: Optional[str] = None) -> ParsedVoiceCommand:
    """
    Public entry point used by the application.

    Keeps the same output schema as before while delegating work to small,
    testable helpers.
    """
    language = detect_language(text, hint=language_hint)
    logger.debug("Parsing voice command", extra={"language": language, "text": text})

    # Try OpenAI first if enabled; fall back to rules.
    parsed = _openai_parse(text, language)
    if parsed:
        if not parsed.category or parsed.category == "other":
            parsed.category = categorize_item(parsed.item)
        return parsed

    action = detect_intent(text, language)
    logger.debug("Text to filters", extra={"text": text})
    filters = extract_filters(text)
    
    # We must extract filters BEFORE quantity, otherwise 'cheaper than 4 dollars'
    # will have '4' stripped out by extract_quantity, failing the price regex.
    quantity, cleaned_text = extract_quantity(text, language)
    item = extract_item(cleaned_text, language)
    category = categorize_item(item)

    if action in {"remove", "modify"} and not item:
        # E.g. "remove it" – keep item empty, caller can handle.
        quantity = max(1, quantity)

    return ParsedVoiceCommand(
        action=action,
        item=item,
        quantity=max(1, quantity),
        category=category,
        filters=Filters(brand=filters.brand, price_max=filters.price_max),
        language=language,
        raw_text=text,
    )

