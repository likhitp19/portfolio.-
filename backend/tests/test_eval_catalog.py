import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.store import clear_threads

client = TestClient(app)
CATALOG = json.loads((Path(__file__).resolve().parents[2] / "eval" / "catalog.json").read_text())


def setup_function() -> None:
    clear_threads()


def test_eval_catalog_routing_and_cleanliness() -> None:
    for item in CATALOG["cases"]:
        payload = {"message": item["query"]}
        if item.get("year"):
            payload["year"] = item["year"]
        body = client.post("/api/chat", json=payload).json()
        trace = body["trace"]
        tools = [call["tool"] for call in trace["api_calls"]]
        for forbidden in item["forbidden_tools"]:
            assert forbidden not in tools, (item["id"], tools)
        assert trace["routing"]["chosen_node"] == item["expected_route"], item["id"]
        assert trace["routing"]["intent"] == item["expected_intent"], (item["id"], trace["routing"])
        if item["expected_route"] == "generalist_direct":
            assert tools == []
        if item["implemented"] is True and item["required_tools"]:
            for required in item["required_tools"]:
                assert required in tools, (item["id"], tools)
            assert trace["execution_trace"], item["id"]


def test_eval_unimplemented_h2h_does_not_call_laps() -> None:
    item = next(c for c in CATALOG["cases"] if c["id"] == 4)
    body = client.post("/api/chat", json={"message": item["query"], "year": 2023}).json()
    tools = [call["tool"] for call in body["trace"]["api_calls"]]
    assert "get_laps" not in tools
    text = body["answer"].lower()
    assert "missing" in text or body["trace"]["missing_inputs"] or "pending full telemetry" in text
