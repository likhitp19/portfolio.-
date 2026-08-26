#!/usr/bin/env python3
"""Temporary live end-to-end Protest Engine smoke test (Spa Turn 5 / cars 44 & 63).

Usage (from ``backend/``)::

    python scripts/test_live_steward.py

Requires keys in ``.env`` (Pinecone, OpenRouter). Prints ProtestDossier JSON.
Do not commit secrets. Delete or keep as a manual smoke tool after demos.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.agents.steward_graph import build_steward_graph, initial_steward_state  # noqa: E402
from app.config import settings  # noqa: E402
from app.integrations.openf1 import OpenF1Client  # noqa: E402
from app.services.rag_service import retrieve_regulations  # noqa: E402


async def main() -> int:
    print("=== Live steward smoke test ===")
    print("pinecone_key_set:", bool(settings.pinecone_key))
    print("openrouter_key_set:", bool(settings.openrouter_key))
    print("index:", settings.pinecone_index, "ns:", settings.pinecone_namespace)

    print("\n--- Pinecone retrieve probe ---")
    hits = retrieve_regulations("causing a collision Article 14 Right of Review", top_k=3)
    for hit in hits:
        print(
            json.dumps(
                {
                    "source": hit.get("source"),
                    "source_document": hit.get("source_document"),
                    "page_number": hit.get("page_number"),
                    "article": hit.get("article") or hit.get("title"),
                    "score": hit.get("score"),
                    "text_preview": (hit.get("text") or "")[:160].replace("\n", " "),
                },
                ensure_ascii=False,
            )
        )
    pinecone_hit = any(hit.get("source") == "pinecone" for hit in hits)
    print("pinecone_hits:", pinecone_hit, "total:", len(hits))

    print("\n--- steward_graph invoke (Spa Turn 5, cars 63/44, lap 1) ---")
    openf1 = OpenF1Client()
    try:
        graph = build_steward_graph(openf1=openf1)
        state = initial_steward_state(
            year=2024,
            circuit="Spa",
            incident_hint=(
                "Spa-Francorchamps Turn 5 lap 1: Car 63 on the outside of Car 44; "
                "alleged understeer / failure to leave racing room / possible collision."
            ),
            live_feed={
                "session_type": "Race",
                "lap_number": 1,
                "involved_driver_numbers": [63, 44],
                "timing_note": "Live timing: Car 63 Russell outside Car 44 Hamilton at Turn 5 lap 1.",
            },
            filing_team="Mercedes-AMG Petronas Formula One Team",
            filing_type="protest",
        )
        result = await graph.ainvoke(state)
    finally:
        await openf1.aclose()
    dossier = result.get("protest_dossier") or {}
    rules = result.get("retrieved_rules") or []
    print("retrieved_rules:", len(rules))
    print("rule_sources:", sorted({str(r.get("source")) for r in rules}))
    print("telemetry_degraded:", result.get("telemetry_degraded"))
    print("telemetry_summary_preview:", (result.get("telemetry_summary") or "")[:300])
    print("\n=== ProtestDossier JSON ===")
    print(json.dumps(dossier, indent=2, ensure_ascii=False))

    violations = dossier.get("regulatory_violations") or []
    ok_objects = violations and all(isinstance(v, dict) for v in violations)
    has_quotes = ok_objects and all(v.get("exact_quote") for v in violations)
    has_pages = ok_objects and all("page_number" in v for v in violations)
    print("\n=== Smoke checks ===")
    print("citation_objects:", ok_objects)
    print("exact_quotes_present:", has_quotes)
    print("page_numbers_present:", has_pages)
    print("success_probability:", dossier.get("success_probability"))
    print("evidence_items:", len(dossier.get("required_telemetry_evidence") or []))
    return 0 if ok_objects and has_quotes else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
