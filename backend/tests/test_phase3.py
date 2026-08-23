from fastapi.testclient import TestClient

from app.main import app
from app.store import clear_threads
from tests.fakes import FakeOpenF1Client

client = TestClient(app)


def setup_function() -> None:
    clear_threads()


def test_seasons_and_meetings() -> None:
    seasons = client.get("/api/seasons").json()
    assert 2024 in seasons["years"]
    assert len(seasons["years"]) == 10
    meetings = client.get("/api/meetings?year=2024").json()
    assert len(meetings) == 2
    assert meetings[0]["circuit_short_name"] == "Sakhir"


def test_championship_and_summary_chart_ready() -> None:
    drivers = client.get("/api/championship/drivers?year=2024").json()
    assert drivers[0]["full_name"] == "Max Verstappen"
    assert drivers[0]["points"] == 43
    constructors = client.get("/api/championship/constructors?year=2024").json()
    assert constructors[0]["team_name"] == "McLaren"
    assert constructors[0]["points"] == 66
    summary = client.get("/api/championship/summary?year=2024").json()
    assert summary["leader_name"] == "Max Verstappen"
    assert summary["race_count"] == 2
    assert summary["points_gap"] == 7


def test_progression_top_five_series() -> None:
    body = client.get("/api/standings/progression?year=2024").json()
    assert len(body["circuits"]) == 2
    assert len(body["series"]) == 5
    max_series = next(s for s in body["series"] if s["driver"] == "Max Verstappen")
    assert max_series["points"] == [25, 43]


def test_constructor_table_is_not_driver_points() -> None:
    drivers = client.get("/api/championship/drivers?year=2024").json()
    constructors = client.get("/api/championship/constructors?year=2024").json()
    assert len(drivers) == 5
    assert "Sergio Perez" not in {d["full_name"] for d in drivers}
    assert "driver_number" not in constructors[0]
    assert constructors[0]["points"] != drivers[0]["points"]
    assert constructors[0]["team_name"] != drivers[0]["full_name"]


def test_dashboard_payload_changes_with_meeting_key() -> None:
    season = client.get("/api/dashboard?year=2024").json()
    bahrain = client.get("/api/dashboard?year=2024&meeting_key=1").json()
    jeddah = client.get("/api/dashboard?year=2024&meeting_key=2").json()
    assert bahrain["meeting_key"] == 1
    assert jeddah["meeting_key"] == 2
    assert bahrain["drivers"][0]["points"] == 25
    assert jeddah["drivers"][0]["points"] == 43
    assert bahrain["constructors"][0]["points"] != jeddah["constructors"][0]["points"]
    assert bahrain["summary"]["race_count"] == 1
    assert season["summary"]["race_count"] == 2
    assert "timeline" not in season


def test_summary_includes_insights() -> None:
    summary = client.get("/api/championship/summary?year=2024").json()
    assert summary["fastest_lap_driver"]
    assert summary["fastest_lap_duration"] == 91.2
    assert summary["total_dnfs"] == 2
    assert summary["top3_finishes"]


def test_chat_chitchat_skips_openf1() -> None:
    response = client.post("/api/chat", json={"message": "What can you do?"})
    body = response.json()
    assert body["trace"]["routing"]["chosen_node"] == "generalist_direct"
    assert body["trace"]["api_calls"] == []
    assert body["trace"]["routing"]["rationale"]


def test_chat_comparative_uses_multiple_championship_calls() -> None:
    response = client.post(
        "/api/chat",
        json={"message": "Compare top 3 driver points after the first vs last race of 2024.", "year": 2024},
    )
    body = response.json()
    assert response.status_code == 200
    tools = [c["tool"] for c in body["trace"]["api_calls"]]
    assert "list_meetings" in tools
    assert tools.count("get_championship_drivers") >= 2
    pipeline_names = [p["name"] for p in body["trace"]["pipelines"]]
    assert "championship_compare" in pipeline_names
    assert "first" in body["answer"].lower() or "latest" in body["answer"].lower()


def test_chat_meeting_scope_uses_race_control(fake_openf1: FakeOpenF1Client) -> None:
    response = client.post(
        "/api/chat",
        json={"message": "What happened at this circuit?", "year": 2024, "meeting_key": 1},
    )
    body = response.json()
    tools = [c["tool"] for c in body["trace"]["api_calls"]]
    assert "get_race_control" in tools
    assert "list_sessions" in tools
    assert "get_championship_drivers" not in tools
    params = [c["params"] for c in body["trace"]["api_calls"] if c["tool"] == "get_race_control"]
    assert params[0].get("meeting_key") == 1


def test_tool_error_is_visible_in_trace(fake_openf1: FakeOpenF1Client) -> None:
    fake_openf1.fail_resource = "list_meetings"
    response = client.post(
        "/api/chat",
        json={"message": "Show championship standings", "year": 2024},
    )
    calls = response.json()["trace"]["api_calls"]
    assert any(c["status"] == "error" for c in calls)


def test_dashboard_overview_endpoint() -> None:
    body = client.get("/api/dashboard?year=2024").json()
    assert body["year"] == 2024
    assert len(body["meetings"]) == 2
    assert body["drivers"][0]["full_name"] == "Max Verstappen"
    assert len(body["progression"]["series"]) == 5


def test_constructor_progression_uses_team_points_not_drivers() -> None:
    body = client.get("/api/dashboard?year=2024").json()
    series = body["constructor_progression"]["series"]
    names = {item["driver"] for item in series}
    assert "Max Verstappen" not in names
    assert "Lando Norris" not in names
    assert "McLaren" in names
    mclaren = next(item for item in series if item["driver"] == "McLaren")
    assert mclaren["points"] == [30, 66]


def test_dashboard_live_lock_error_code(fake_openf1: FakeOpenF1Client) -> None:
    fake_openf1.fail_resource = "list_meetings"
    fake_openf1.fail_status = 401
    response = client.get("/api/dashboard?year=2024")
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["code"] == "F1_LIVE_LOCK"
    assert "session" in detail["message"].lower()
