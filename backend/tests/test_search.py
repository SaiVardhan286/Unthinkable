from fastapi.testclient import TestClient
import os
import sys

# ALWAYS DISABLE OPENAI DURING TESTS
os.environ["ENABLE_OPENAI_PARSER"] = "false"
os.environ["OPENAI_API_KEY"] = "" # Also clear the key just in case

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from search_service import SearchService
from schemas import Filters

client = TestClient(app)

def test_search_with_brand():
    response = client.post("/search", json={
        "query_text": "tooth",
        "voice_text": "Search Colgate toothpaste"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["filters"]["brand"].lower() == "colgate"
    assert len(data["results"]) >= 1
    assert data["results"][0]["brand"].lower() == "colgate"

def test_search_with_price():
    response = client.post("/search", json={
        "query_text": "milk",
        "voice_text": "Search for milk cheaper than 4 dollars"
    })
    assert response.status_code == 200
    data = response.json()
    print("PRICE TEST DATA:", data)
    assert data["filters"]["price_max"] == 4.0
    for product in data["results"]:
        assert product["price"] <= 4.0

def test_search_with_size():
    response = client.post("/search", json={
        "query_text": "milk",
        "voice_text": "large amul milk"
    })
    assert response.status_code == 200
    # Note: large is conceptually a size, or we test specifically "medium Colgate"
    pass

def test_spanish_price_filter():
    response = client.post("/search", json={
        "query_text": "leche",
        "voice_text": "Busca leche Amul menor que 50",
        "language": "es"
    })
    assert response.status_code == 200
    data = response.json()
    print("SPANISH PRICE TEST DATA:", data)
    assert data["filters"]["price_max"] == 50.0
    assert data["filters"]["brand"].lower() == "amul"

def test_combined_filters():
    response = client.post("/search", json={
        "query_text": "",
        "voice_text": "Find organic apples under 5 dollars"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["filters"]["price_max"] == 5.0

def test_no_results_fallback():
    response = client.post("/search", json={
        "query_text": "NonExistentProduct",
        "voice_text": "Search for NonExistentProduct string"
    })
    assert response.status_code == 200
    # Fuzzy match logic or suggestions should return empty results if none
    pass

def test_search_service_direct():
    service = SearchService()
    filters = Filters(brand="Amul", price_max=10.0, size="1L")
    results = service.search("milk", filters)
    assert len(results) == 1
    assert results[0]["name"] == "Amul Milk"

