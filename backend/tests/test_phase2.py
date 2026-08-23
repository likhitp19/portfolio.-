from __future__ import annotations

import inspect

import pytest
from fastapi.testclient import TestClient

from app.agents.graph import compiled_graph
from app.agents.nodes.technical_manager import TRACE_KEYS
from app.integrations.openf1 import OpenF1Client
from app.main import app
from app.store import clear_threads

client = TestClient(app)

DASHBOARD_GETS = [
    "/api/seasons",
    "/api/meetings?year=2024",
    "/api/championship/drivers?year=2024",
    "/api/championship/constructors?year=2024",
    "/api/championship/summary?year=2024",
    "/api/standings/progression?year=2024",
    "/api/dashboard?year=2024",
]


@pytest.fixture(autouse=True)
def _reset_threads() -> None:
    clear_threads()
    yield
    clear_threads()


def test_openapi_lists_phase2_routes() -> None:
    paths = client.get("/openapi.json").json()["paths"]
    for path in [
        "/health",
        "/api/seasons",
        "/api/meetings",
        "/api/championship/drivers",
        "/api/championship/constructors",
        "/api/championship/summary",
        "/api/standings/progression",
        "/api/dashboard",
        "/api/chat",
        "/api/chat/{thread_id}",
    ]:
        assert path in paths
    assert "/api/events/timeline" not in paths


@pytest.mark.parametrize("path", DASHBOARD_GETS)
def test_dashboard_stubs_return_200(path: str) -> None:
    response = client.get(path)
    assert response.status_code == 200


def test_chat_returns_well_formed_trace() -> None:
    response = client.post("/api/chat", json={"message": "hello", "year": 2024})
    assert response.status_code == 200
    body = response.json()
    assert body["thread_id"]
    assert isinstance(body["answer"], str)
    trace = body["trace"]
    for key in TRACE_KEYS:
        assert key in trace
    assert trace["api_calls"] == []
    assert isinstance(trace["reasoning_path"], list)
    assert trace["pipelines"] == []
    assert set(trace["routing"].keys()) >= {"intent", "chosen_node", "rationale"}
    assert trace["routing"]["chosen_node"] == "generalist_direct"

    snapshot = client.get(f"/api/chat/{body['thread_id']}")
    assert snapshot.status_code == 200
    assert snapshot.json()["thread_id"] == body["thread_id"]
    assert snapshot.json()["trace"] == trace


def test_unknown_thread_404() -> None:
    assert client.get("/api/chat/missing").status_code == 404


def test_graph_topology_includes_delegation_loop() -> None:
    mermaid = compiled_graph.get_graph().draw_mermaid()
    for node in ("generalist", "data_analyst", "researcher", "tools", "technical_manager"):
        assert node in mermaid
    assert "tools" in mermaid and "data_analyst" in mermaid


def test_openf1_catalog_methods_exist() -> None:
    api = OpenF1Client("https://api.openf1.org/v1")
    methods = [
        "list_meetings",
        "list_sessions",
        "get_drivers",
        "get_championship_drivers",
        "get_championship_teams",
        "get_session_result",
        "get_laps",
        "get_position",
        "get_race_control",
        "get_weather",
    ]
    assert [m for m in methods if inspect.iscoroutinefunction(getattr(api, m))] == methods
