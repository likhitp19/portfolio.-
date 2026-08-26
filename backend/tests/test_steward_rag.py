"""Phase 1 / Phase 2 offline tests for PDF chunking, RAG fallback, and dossier schema."""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.schemas.steward import ProtestDossier, RegulatoryCitation
from app.services.legal_chunking import chunk_pdf, promote_legal_headers
from app.services.rag_service import RuleRetriever, retrieve_regulations
from app.tools.openf1 import get_race_control, get_team_radio
from tests.fakes import FakeOpenF1Client

PDF_PATH = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "data"
    / "pdfs"
    / "FIA_2026_F1_Sporting_Regulations_Iss08.pdf"
)


def test_promote_legal_headers_marks_articles() -> None:
    raw = "ARTICLE 14\nRight of Review text.\n\nCHAPTER IV\nDriving standards."
    md = promote_legal_headers(raw)
    assert "## ARTICLE 14" in md
    assert "## CHAPTER IV" in md


def test_pdf_chunk_metadata_has_page_and_source() -> None:
    assert PDF_PATH.is_file(), "Expected FIA PDF under backend/app/data/pdfs/"
    chunks = chunk_pdf(PDF_PATH)
    assert chunks, "Expected at least one chunk from the FIA PDF"
    sample = chunks[0]
    assert isinstance(sample["page_number"], int) and sample["page_number"] >= 1
    assert sample["source"] == PDF_PATH.name
    assert sample["source_document"] == PDF_PATH.name
    assert sample.get("article")
    assert sample.get("text")
    # Spot-check deeper pages still carry page metadata.
    mid = chunks[len(chunks) // 2]
    assert mid["page_number"] >= 1
    assert mid["source_document"] == PDF_PATH.name


def test_retrieve_regulations_offline_without_pinecone(monkeypatch) -> None:
    monkeypatch.setattr("app.services.rag_service.settings.pinecone_api_key", "")
    hits = retrieve_regulations("Article 14 Right of Review significant new element", top_k=3)
    assert hits
    for hit in hits:
        assert "text" in hit
        assert "source_document" in hit
        assert "page_number" in hit
    blob = " ".join((hit.get("title") or "") + " " + (hit.get("text") or "") for hit in hits).lower()
    assert "article 14" in blob or "right of review" in blob


def test_retrieve_regulations_uses_keyword_fallback_explicitly() -> None:
    retriever = RuleRetriever(use_chroma=False, use_pinecone=False)
    hits = retriever.retrieve_rules("causing a collision Appendix L Chapter IV", top_k=3)
    assert hits
    assert hits[0]["source"] == "keyword"
    assert hits[0]["source_document"]


def test_protest_dossier_schema_validates_citations() -> None:
    dossier = ProtestDossier.model_validate(
        {
            "filing_type": "protest",
            "filing_team": "Mercedes-AMG Petronas Formula One Team",
            "competitor_team": "Competitor",
            "primary_claim": "Car 44 failed to leave racing room at Turn 5.",
            "regulatory_violations": [
                {
                    "article_name": "ARTICLE 14",
                    "exact_quote": "A significant and relevant new element",
                    "page_number": 42,
                    "source_document": "FIA_2026_F1_Sporting_Regulations_Iss08.pdf",
                }
            ],
            "available_evidence_summary": "Broadcast + coarse OpenF1",
            "required_telemetry_evidence": [
                {
                    "id": "steering_apex",
                    "label": "Steering angle",
                    "rationale": "Micro-telemetry missing",
                    "status": "pending_phase2",
                    "phase2_schema_ref": "steering_angle_deg",
                }
            ],
            "success_probability": "Low",
            "legal_risk_notes": "Article 14 significance risk",
            "recommended_next_step": "Ingest Phase 2 telemetry",
        }
    )
    assert isinstance(dossier.regulatory_violations[0], RegulatoryCitation)
    assert dossier.regulatory_violations[0].page_number == 42
    assert dossier.success_probability == "Low"
    payload = dossier.model_dump()
    assert payload["regulatory_violations"][0]["exact_quote"]
    assert payload["required_telemetry_evidence"][0]["status"] == "pending_phase2"


def test_protest_dossier_coerces_string_violations() -> None:
    dossier = ProtestDossier.model_validate(
        {
            "primary_claim": "Claim",
            "regulatory_violations": ["ISC Appendix L teaching paraphrase"],
            "success_probability": "Low",
        }
    )
    assert len(dossier.regulatory_violations) == 1
    assert dossier.regulatory_violations[0].exact_quote.startswith("ISC Appendix L")


def test_openf1_race_control_and_team_radio_tools() -> None:
    client = FakeOpenF1Client()

    async def run():
        control = await get_race_control(101, 1, openf1=client)
        radio = await get_team_radio(101, 63, openf1=client)
        return control, radio

    control, radio = asyncio.run(run())
    assert control
    assert any("INVESTIGATION" in str(row.get("message") or "").upper() or row.get("flag") for row in control)
    assert radio
    assert radio[0]["driver_number"] == 63
    assert radio[0].get("recording_url")
