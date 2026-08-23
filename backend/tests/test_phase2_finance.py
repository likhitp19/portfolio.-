from app.runtime import get_search_client
from app.services.commercial import lookup_valuation
from app.services.fact_store import FactStore
from fastapi.testclient import TestClient

from app.main import app
from app.store import clear_threads

client = TestClient(app)


def setup_function() -> None:
    clear_threads()


def test_constructor_finance_not_driver_table() -> None:
    drivers = client.get("/api/championship/drivers?year=2024").json()
    constructors = client.get("/api/championship/constructors?year=2024").json()
    assert "driver_number" not in constructors[0]
    assert constructors[0]["points"] != drivers[0]["points"]
    mclaren = next(row for row in constructors if row["team_name"] == "McLaren")
    assert mclaren["budget_cap_usd"] == 135000000
    assert mclaren["cost_per_point"] == 135000000 / 66
    assert mclaren["valuation_usd"] == 2000000000
    assert mclaren["valuation"]["source_url"]
    assert mclaren["wins"] == 0


def test_red_bull_wins_and_cpp() -> None:
    constructors = client.get("/api/championship/constructors?year=2024").json()
    rbr = next(row for row in constructors if row["team_name"] == "Red Bull Racing")
    assert rbr["wins"] == 2
    assert rbr["avg_wins"] == 1.0
    assert rbr["cost_per_point"] == 135000000 / 61


def test_dashboard_does_not_call_search() -> None:
    search = get_search_client()
    search.calls.clear()
    client.get("/api/dashboard?year=2024")
    assert search.calls == []


def test_frozen_year_not_overwritten_without_force() -> None:
    store = FactStore(":memory:")
    first = {
        "entity_type": "constructor",
        "entity_key": "mclaren",
        "season_year": 2024,
        "metric": "valuation_usd",
        "value_usd": 1,
        "frozen": True,
    }
    assert store.upsert(first, force=True) is True
    second = dict(first)
    second["value_usd"] = 99
    assert store.upsert(second, force=False) is False
    assert store.get("constructor", "mclaren", 2024, "valuation_usd")["value_usd"] == 1
    assert store.upsert(second, force=True) is True
    assert store.get("constructor", "mclaren", 2024, "valuation_usd")["value_usd"] == 99


def test_midfield_constructors_have_seeded_valuations() -> None:
    store = FactStore(":memory:")
    for team in ("alpine", "haas", "williams", "aston martin", "rb", "sauber"):
        row = lookup_valuation(store, team, 2025)
        assert row is not None
        assert row.get("value_usd")
        assert row.get("status") != "defaulted"
