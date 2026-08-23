from app.agents.planning import classify_intent
from app.data.mock_financial import mock_facts_for_year
from app.integrations.jolpica import merge_ergast_race_pages
from fastapi.testclient import TestClient

from app.main import app
from app.store import clear_threads

client = TestClient(app)


def setup_function() -> None:
    clear_threads()


def test_quantitative_queries_are_not_regulatory() -> None:
    assert classify_intent({"user_query": "Which driver has the best salary per point in 2024?"}) == "driver_roi"
    assert classify_intent({"user_query": "McLaren vs Ferrari cost efficiency 2023"}) == "constructor_finance"
    assert classify_intent({"user_query": "Show 2024 championship rankings by constructor"}) == "constructor_finance"


def test_plain_budget_cap_stays_regulatory() -> None:
    assert classify_intent({"user_query": "What is the F1 budget cap?"}) == "regulatory_knowledge"


def test_ergast_pages_merge_all_grand_prix() -> None:
    by_round = {}
    merge_ergast_race_pages(
        by_round,
        [{"round": "1", "Results": [{"position": "1", "Constructor": {"name": "McLaren"}}]}],
    )
    merge_ergast_race_pages(
        by_round,
        [{"round": "2", "Results": [{"position": "1", "Constructor": {"name": "Ferrari"}}]}],
    )
    assert len(by_round) == 2
    assert len(by_round["1"]["Results"]) == 1


def test_mock_financial_covers_2023_and_2024() -> None:
    rows_2023 = mock_facts_for_year(2023)
    rows_2024 = mock_facts_for_year(2024)
    assert any(row["metric"] == "salary_usd" and row["entity_key"] == "1" for row in rows_2023)
    assert any(row["metric"] == "valuation_usd" for row in rows_2024)


def test_roi_chat_routes_to_data_analyst() -> None:
    body = client.post(
        "/api/chat",
        json={"message": "Highest salary per championship point in 2024?", "year": 2024},
    ).json()
    assert body["trace"]["routing"]["chosen_node"] == "data_analyst"
    assert body["trace"]["routing"]["intent"] == "driver_roi"
