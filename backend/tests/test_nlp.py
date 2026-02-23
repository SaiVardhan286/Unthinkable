from __future__ import annotations

from nlp import detect_intent, detect_language, extract_filters, extract_item, extract_quantity, parse_voice_command


def test_language_detection_en_vs_es():
    assert detect_language("Buy two apples") == "en"
    assert detect_language("Necesito leche", None) == "es"


def test_intent_detection_basic():
    assert detect_intent("add milk", "en") == "add"
    assert detect_intent("remove milk", "en") == "remove"
    assert detect_intent("busca leche", "es") == "search"


def test_intent_negation_does_not_mutate():
    # "don't add milk" should be treated as non-mutating (search) intent
    assert detect_intent("don't add milk", "en") == "search"


def test_quantity_digits_and_words():
    assert extract_quantity("buy 3 apples", "en")[0] == 3
    assert extract_quantity("buy two apples", "en")[0] == 2
    assert extract_quantity("compra dos manzanas", "es")[0] == 2


def test_item_extraction():
    item = extract_item("Buy 2 bottles of water", "en")
    assert "water" in item


def test_filters_parsing_brand_and_price():
    f = extract_filters("Search milk brand DairyPure under 5")
    assert f.brand.lower() == "dairypure"
    assert f.price_max == 5.0


def test_parse_voice_command_multilingual():
    parsed_en = parse_voice_command("Buy 2 bottles of water", language_hint="en")
    assert parsed_en.action == "add"
    assert parsed_en.quantity == 2
    assert "water" in parsed_en.item

    parsed_es = parse_voice_command("Busca leche hasta 5", language_hint="es")
    assert parsed_es.action == "search"
    assert "leche" in parsed_es.item or "milk" in parsed_es.item
    assert parsed_es.filters.price_max == 5.0


def test_spanish_quantity_and_intent():
    parsed = parse_voice_command("Agrega dos manzanas", language_hint="es")
    assert parsed.action == "add"
    assert parsed.quantity == 2

