from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from app.agents.steward_graph import (
    build_steward_graph,
    extract_json_object,
    initial_steward_state,
)
from app.integrations.openf1 import OpenF1HTTPError
from app.main import app
from app.services.rag_service import RuleRetriever, retrieve_rules
from tests.fakes import FakeOpenF1Client


def test_steward_graph_joins_openf1_car_data() -> None:
    async def vision(_state):
        return {
            "session_type": "Race",
            "lap_number": 18,
            "involved_driver_numbers": [63, 44],
            "spatial_description": "Car 63 was on the inside, Car 44 turned in from the outside.",
        }

    async def reason(state):
        return {
            "incident": state.get("spatial_description") or "",
            "rule_cited": (state.get("retrieved_rules") or [{}])[0].get("title") or "outside",
            "telemetry_facts": state.get("telemetry_summary") or "",
            "verdict": "Racing Incident",
            "penalty": "None",
        }

    async def run():
        graph = build_steward_graph(openf1=FakeOpenF1Client(), vision_fn=vision, reason_fn=reason)
        return await graph.ainvoke(
            initial_steward_state(
                clip_url="https://example.com/clip.mp4",
                year=2024,
                circuit="Sakhir",
                incident_hint="Turn 1 contact",
            )
        )

    result = asyncio.run(run())
    assert result["vision"]["involved_driver_numbers"] == [63, 44]
    assert result["telemetry_degraded"] is False
    assert "Driver 63" in result["telemetry_summary"]
    assert result["verdict"]["verdict"] == "Racing Incident"
    stages = [item["stage"] for item in result["pipeline"]]
    assert stages == ["vision", "telemetry", "rules", "reasoning"]
    assert result["retrieved_rules"]


def test_steward_graph_degrades_when_car_data_missing() -> None:
    async def vision(_state):
        return {
            "session_type": "Race",
            "lap_number": 18,
            "involved_driver_numbers": [63, 44],
            "spatial_description": "Car 63 was on the inside.",
        }

    async def reason(_state):
        return {
            "incident": "Inside pass",
            "rule_cited": "Overtaking on the inside",
            "telemetry_facts": "I measured 330 km/h",
            "verdict": "Causing a collision",
            "penalty": "10 second time penalty",
        }

    async def run():
        client = FakeOpenF1Client(fail_resource="get_car_data", fail_status=500)
        graph = build_steward_graph(openf1=client, vision_fn=vision, reason_fn=reason)
        return await graph.ainvoke(
            initial_steward_state(clip_url="https://example.com/clip.mp4", year=2024, circuit="Sakhir")
        )

    result = asyncio.run(run())
    assert result["telemetry_degraded"] is True
    facts = result["verdict"]["telemetry_facts"].lower()
    assert "unavailable" in facts or "not available" in facts


def test_steward_live_lock_degrades() -> None:
    async def vision(_state):
        return {
            "session_type": "Race",
            "lap_number": 1,
            "involved_driver_numbers": [1],
            "spatial_description": "Start contact.",
        }

    async def reason(state):
        return {
            "incident": "Start contact",
            "rule_cited": "First-lap incidents",
            "telemetry_facts": state.get("telemetry_summary") or "",
            "verdict": "Insufficient evidence",
            "penalty": "To be reviewed with full onboard",
        }

    class Locked(FakeOpenF1Client):
        async def list_sessions(self, **params):
            self._record("list_sessions", **params)
            raise OpenF1HTTPError(401, "Live F1 session in progress.")

    async def run():
        graph = build_steward_graph(openf1=Locked(), vision_fn=vision, reason_fn=reason)
        return await graph.ainvoke(initial_steward_state(incident_hint="Car 1 start", year=2024, circuit="Sakhir"))

    result = asyncio.run(run())
    assert result["telemetry_degraded"] is True


def test_retrieve_rules_outside_overtake() -> None:
    hits = retrieve_rules("overtaking on the outside leaving room at the apex", top_k=3)
    assert hits
    blob = " ".join(hit["text"].lower() + hit["title"].lower() for hit in hits)
    assert "outside" in blob


def test_rule_retriever_keyword_only() -> None:
    retriever = RuleRetriever(use_chroma=False)
    hits = retriever.retrieve_rules("blue flags lapped cars", top_k=2)
    assert any("blue" in hit["title"].lower() or "blue" in hit["text"].lower() for hit in hits)


def test_extract_json_from_r1_think_block() -> None:
    raw = '<think>scratch</think>```json\n{"incident": "x", "verdict": "Racing Incident"}\n```'
    data = extract_json_object(raw)
    assert data["verdict"] == "Racing Incident"


def test_analyze_clip_requires_input() -> None:
    client = TestClient(app)
    response = client.post("/api/steward/analyze_clip", json={})
    assert response.status_code == 422


def test_steward_live_feed_unlocks_telemetry_when_vision_misses_drivers() -> None:
    """Simulates live timing overlay filling gaps when broadcast vision is too wide."""

    async def vision(_state):
        # Wide TV angle: sees contact but not car numbers (like testf1incident1.mp4).
        return {
            "session_type": "Race",
            "lap_number": None,
            "involved_driver_numbers": [],
            "spatial_description": "Opening-lap contact at a high-speed corner; car numbers not readable on broadcast.",
        }

    async def reason(state):
        spatial = state.get("spatial_description") or ""
        return {
            "primary_claim": "Car 44 failed to leave racing room for Car 63 at Turn 5.",
            "regulatory_violations": [
                "ISC Appendix L, Chapter IV, Article 2 d) — causing a collision (teaching paraphrase)",
                "ISC Article 13 — Protests (teaching paraphrase)",
            ],
            "available_evidence_summary": state.get("telemetry_summary") or "",
            "required_telemetry_evidence": [],
            "success_probability": "Low",
            "legal_risk_notes": "Micro-telemetry pending.",
            "recommended_next_step": "Ingest Phase 2 steering / brake traces.",
            "incident": spatial[:240],
            "rule_cited": "Overtaking on the outside",
            "telemetry_facts": state.get("telemetry_summary") or "",
            "verdict": "Insufficient evidence for Protest",
            "penalty": "5 second time penalty (sought)",
        }

    async def run():
        graph = build_steward_graph(openf1=FakeOpenF1Client(), vision_fn=vision, reason_fn=reason)
        return await graph.ainvoke(
            initial_steward_state(
                clip_url="https://example.com/spa-lap1.mp4",
                year=2024,
                circuit="Sakhir",
                live_feed={
                    "session_type": "Race",
                    "lap_number": 1,
                    "involved_driver_numbers": [63, 44],
                    "timing_note": (
                        "Live timing: Car 63 Russell on the outside of Car 44 Hamilton at Turn 5 on lap 1."
                    ),
                },
            )
        )

    result = asyncio.run(run())
    assert result["vision"]["involved_driver_numbers"] == [63, 44]
    assert result["vision"]["lap_number"] == 1
    assert "Turn 5" in result["spatial_description"]
    assert result["telemetry_degraded"] is False
    assert "Driver 63" in result["telemetry_summary"]
    assert any("Live feed supplied" in item for item in result["assumptions"])
    dossier = result["protest_dossier"]
    assert dossier["primary_claim"]
    assert dossier["success_probability"] in {"Low", "Medium", "High"}
    evidence = dossier["required_telemetry_evidence"]
    assert evidence
    assert any(item["status"] == "pending_phase2" for item in evidence)
    assert any(item["status"] == "present" for item in evidence)


def test_protest_dossier_requests_phase2_when_telemetry_coarse() -> None:
    from app.agents.steward_graph import _heuristic_dossier

    async def vision(_state):
        return {
            "session_type": "Race",
            "lap_number": 1,
            "involved_driver_numbers": [63, 44],
            "spatial_description": "Car 63 outside Car 44 at Turn 5; alleged understeer contact.",
        }

    async def reason(state):
        return _heuristic_dossier(state, "unit-test")

    async def run():
        client = FakeOpenF1Client(fail_resource="get_car_data", fail_status=500)
        graph = build_steward_graph(openf1=client, vision_fn=vision, reason_fn=reason)
        return await graph.ainvoke(
            initial_steward_state(
                clip_url="https://example.com/clip.mp4",
                year=2024,
                circuit="Sakhir",
                filing_team="Mercedes-AMG Petronas Formula One Team",
                filing_type="protest",
            )
        )

    result = asyncio.run(run())
    dossier = result["protest_dossier"]
    assert dossier["filing_team"].startswith("Mercedes")
    assert dossier["success_probability"] == "Low"
    pending = [item for item in dossier["required_telemetry_evidence"] if item["status"] == "pending_phase2"]
    assert any("steering" in item["label"].lower() for item in pending)
    assert any(
        "Article 13" in item["article_name"] or "Appendix L" in item["article_name"] or "Article 13" in item["exact_quote"]
        for item in dossier["regulatory_violations"]
    )
    assert all("exact_quote" in item and "page_number" in item for item in dossier["regulatory_violations"])


def test_retrieve_rules_article_14_and_appendix_l() -> None:
    hits = retrieve_rules("Article 14 Right of Review significant new element Appendix L Chapter IV", top_k=4)
    assert hits
    blob = " ".join(hit["text"].lower() + hit["title"].lower() for hit in hits)
    assert "article 14" in blob or "right of review" in blob
    assert "appendix l" in blob or "chapter iv" in blob or "collision" in blob


def test_analyze_clip_accepts_live_feed_without_clip() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/steward/analyze_clip",
        json={
            "year": 2024,
            "circuit": "Sakhir",
            "live_feed": {
                "session_type": "Race",
                "lap_number": 18,
                "involved_driver_numbers": [63, 44],
                "timing_note": "Car 63 on the outside of Car 44 at Turn 5 lap 18.",
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["vision"]["involved_driver_numbers"] == [63, 44]
    assert payload["vision"]["lap_number"] == 18


def test_analyze_clip_vision_only_without_keys() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/steward/analyze_clip",
        json={
            "incident_hint": "Car 63 was on the inside, Car 44 turned in from the outside on lap 18 of the race.",
            "year": 2024,
            "circuit": "Sakhir",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["verdict"]["incident"]
    assert payload["vision"]["involved_driver_numbers"] == [63, 44]
    assert payload["disclaimer"]
