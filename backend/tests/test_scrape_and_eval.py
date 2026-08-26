"""Offline unit tests for FIA sporting scraper filters and RAG eval helpers."""

from __future__ import annotations

from scripts.scrape_fia_sporting import discover_pdf_candidates, is_sporting_document
from scripts.evaluate_rag import CASES, citation_faithfulness, context_precision, quote_verbatim_score


def test_sporting_filter_allows_sporting_and_appendix_l() -> None:
    assert is_sporting_document("2026 Formula 1 Sporting Regulations", "https://fia.com/files/sporting.pdf")
    assert is_sporting_document("Appendix L — Chapter IV", "https://fia.com/docs/appendix-l.pdf")
    assert is_sporting_document("ISC Appendix L", "https://example.com/download?file=appendix_l.pdf")


def test_sporting_filter_rejects_technical_financial_pu() -> None:
    assert not is_sporting_document("2026 Technical Regulations", "https://fia.com/tech.pdf")
    assert not is_sporting_document("Financial Regulations", "https://fia.com/financial.pdf")
    assert not is_sporting_document("Power Unit Regulations", "https://fia.com/pu-regulations.pdf")


def test_discover_pdf_candidates_filters_html() -> None:
    html = """
    <html><body>
      <a href="/files/f1-sporting-2026.pdf" title="F1 Sporting Regulations 2026">Sporting</a>
      <a href="/files/f1-technical-2026.pdf" title="F1 Technical Regulations 2026">Technical</a>
      <a href="https://cdn.example.com/appendix-l.pdf">Appendix L</a>
      <a href="/files/financial.pdf">Financial Regulations</a>
    </body></html>
    """
    found = discover_pdf_candidates(html, "https://www.fia.com/regulation/category/110")
    urls = {item["url"] for item in found}
    assert any("sporting" in url.lower() for url in urls)
    assert any("appendix-l" in url.lower() for url in urls)
    assert not any("technical" in url.lower() for url in urls)
    assert not any("financial" in url.lower() for url in urls)


def test_rag_eval_helpers_score_sporting_hits() -> None:
    hits = [
        {
            "title": "Appendix L Chapter IV Article 2 — Causing a collision",
            "article": "Appendix L Chapter IV",
            "source_document": "fia_driving_standards.md",
            "text": "A driver must not cause a collision. Overtaking and leaving racing room apply.",
            "source": "keyword",
        }
    ]
    assert citation_faithfulness(hits, ("collision", "racing room")) >= 0.9
    assert quote_verbatim_score(hits) == 1.0
    assert context_precision(hits, ("appendix l", "collision")) >= 0.9


def test_rag_eval_cases_defined() -> None:
    assert len(CASES) == 3
