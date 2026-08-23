from fastapi.testclient import TestClient

from app.main import app
from app.store import clear_threads

client = TestClient(app)


def setup_function() -> None:
    clear_threads()


def test_driver_top_five_ordered_with_fer() -> None:
    drivers = client.get("/api/championship/drivers?year=2024").json()
    assert len(drivers) == 5
    assert [d["position"] for d in drivers] == [1, 2, 3, 4, 5]
    maxv = drivers[0]
    assert maxv["full_name"] == "Max Verstappen"
    assert maxv["salary_usd"] == 55000000
    assert maxv["financial_efficiency"] == 55000000 / 43
    assert maxv["salary"]["status"] == "estimate"
    piastri = next(d for d in drivers if d["driver_number"] == 81)
    assert piastri["financial_efficiency"] == 3000000 / 30


def test_missing_salary_is_defaulted_not_invented() -> None:
    from app.runtime import get_fact_store

    store = get_fact_store()
    store._conn.execute(
        "DELETE FROM facts WHERE entity_type = 'driver' AND entity_key = '44'"
    )
    store._conn.commit()
    drivers = client.get("/api/championship/drivers?year=2024").json()
    ham = next(d for d in drivers if d["driver_number"] == 44)
    assert ham["salary_usd"] is None
    assert ham["financial_efficiency"] is None
    assert ham["salary"]["status"] == "defaulted"


def test_progression_still_five_series() -> None:
    body = client.get("/api/standings/progression?year=2024").json()
    assert len(body["series"]) == 5
