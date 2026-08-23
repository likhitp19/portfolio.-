from fastapi.testclient import TestClient

from app.agents.planning import classify_intent
from app.main import app
from app.store import clear_threads

client = TestClient(app)

DRIVER_ROI = (
    "Which driver delivered the highest financial ROI in the 2023 season "
    "based on estimated salary versus championship points scored?"
)
MIDFIELD = (
    "If an investor wanted to back the most cost-efficient midfield team "
    "from 2023 for future upside, who would the data suggest and why?"
)
MCLAREN = (
    "Compare the capital efficiency and cost-per-point between McLaren "
    "and Ferrari under the cost cap in 2023."
)


def setup_function() -> None:
    clear_threads()


def test_exact_user_queries_classify_as_finance() -> None:
    assert classify_intent({"user_query": DRIVER_ROI, "season_year": 2024}) == "driver_roi"
    assert classify_intent({"user_query": MIDFIELD, "season_year": 2024}) == "constructor_finance"
    assert classify_intent({"user_query": MCLAREN, "season_year": 2024}) == "constructor_finance"


def test_midfield_investor_does_not_take_standings_path() -> None:
    body = client.post(
        "/api/chat",
        json={"message": MIDFIELD, "year": 2024},
    ).json()
    tools = [call["tool"] for call in body["trace"]["api_calls"]]
    years = [call.get("params", {}).get("year") for call in body["trace"]["api_calls"]]
    assert body["trace"]["routing"]["intent"] == "constructor_finance"
    assert "list_meetings" not in tools
    assert "get_championship_teams" in tools
    assert "get_finance_estimates" in tools
    assert 2023 in years
    assert 2024 not in years
    assert "championship snapshots" not in body["answer"].lower()
    assert body["trace"]["execution_trace"]
    assert "[Source: Public Financial Benchmarks & Cost Cap Estimates]" in body["answer"]


def test_driver_roi_uses_query_year_not_dashboard_year() -> None:
    body = client.post(
        "/api/chat",
        json={"message": DRIVER_ROI, "year": 2024},
    ).json()
    tools = [call["tool"] for call in body["trace"]["api_calls"]]
    years = [call.get("params", {}).get("year") for call in body["trace"]["api_calls"]]
    assert body["trace"]["routing"]["intent"] == "driver_roi"
    assert "get_championship_drivers" in tools
    assert "get_finance_estimates" in tools
    assert 2023 in years
    assert "list_meetings" not in tools
    assert "[Source: Public Financial Benchmarks & Cost Cap Estimates]" in body["answer"]


def test_h2h_does_not_invent_deltas_or_call_laps() -> None:
    body = client.post(
        "/api/chat",
        json={
            "message": "Compare Charles Leclerc and Carlos Sainz across the 2023 season. What was their qualifying delta and race finish ratio?",
            "year": 2024,
        },
    ).json()
    tools = [call["tool"] for call in body["trace"]["api_calls"]]
    years = [call.get("params", {}).get("year") for call in body["trace"]["api_calls"] if call.get("params", {}).get("year")]
    assert body["trace"]["routing"]["intent"] == "teammate_h2h"
    assert "get_laps" not in tools
    assert "will not invent" in body["answer"].lower() or "pending full telemetry" in body["answer"].lower()
    assert 2023 in years or not years
    assert "delta" not in body["answer"].lower() or "not invent" in body["answer"].lower() or "pending" in body["answer"].lower()
