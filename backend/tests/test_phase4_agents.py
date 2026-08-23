from fastapi.testclient import TestClient

from app.main import app
from app.runtime import get_search_client
from app.store import clear_threads

client = TestClient(app)


def setup_function() -> None:
    clear_threads()


def test_greeting_skips_tools() -> None:
    body = client.post("/api/chat", json={"message": "hello"}).json()
    assert body["trace"]["routing"]["chosen_node"] == "generalist_direct"
    assert body["trace"]["api_calls"] == []


def test_constructor_finance_uses_store_not_search() -> None:
    search = get_search_client()
    search.calls.clear()
    body = client.post(
        "/api/chat",
        json={"message": "Which constructor has the best cost-per-point in 2024?", "year": 2024},
    ).json()
    tools = [c["tool"] for c in body["trace"]["api_calls"]]
    assert "get_finance_estimates" in tools
    assert "get_championship_teams" in tools
    assert "search_commercial" not in tools
    assert "finance_fact_store" in [p["name"] for p in body["trace"]["pipelines"]]
    assert search.calls == []
    assert body["trace"]["routing"]["chosen_node"] == "data_analyst"
    assert "cost" in body["answer"].lower() or "point" in body["answer"].lower()


def test_researcher_searches_then_reads_store() -> None:
    body = client.post(
        "/api/chat",
        json={"message": "Look up McLaren F1 team valuation online for 2024", "year": 2024},
    ).json()
    assert body["trace"]["routing"]["chosen_node"] == "researcher"
    tools = [c["tool"] for c in body["trace"]["api_calls"]]
    assert "search_commercial" in tools
    assert "get_finance_estimates" in tools
    assert "search_commercial" in [p["name"] for p in body["trace"]["pipelines"]]
    assert "researcher" in body["answer"].lower() or "search" in body["answer"].lower() or "fact" in body["answer"].lower()
