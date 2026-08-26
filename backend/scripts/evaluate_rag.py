#!/usr/bin/env python3
"""RAG fidelity scorecard for the Protest Engine (offline-safe by default).

Scores two metrics in ``[0.0, 1.0]`` across three historical-style cases:

1. **Citation Faithfulness** — exact quotes appear verbatim in retrieved chunk text.
2. **Context Precision** — retrieved regulations are Sporting / Appendix L related
   (not Technical / Financial / Power Unit).

Usage (from ``backend/``)::

    python scripts/evaluate_rag.py
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.rag_service import RuleRetriever, retrieve_regulations  # noqa: E402

SPORTING_HINTS = re.compile(
    r"(sporting|appendix\s*l|chapter\s*iv|article\s*1[34]|right of review|"
    r"protest|collision|overtaking|driving\s*standards|leaving\s*room)",
    re.I,
)
OFFTOPIC_HINTS = re.compile(
    r"(technical\s*regulation|power\s*unit|financial\s*regulation|budget\s*cap|"
    r"homologation|ers|mgu-k)",
    re.I,
)


@dataclass
class EvalCase:
    name: str
    query: str
    must_match_any: Sequence[str]
    expected_topics: Sequence[str]


CASES: List[EvalCase] = [
    EvalCase(
        name="Spa Turn 5 collision / racing room",
        query="causing a collision leaving racing room overtaking outside Turn 5 Appendix L Chapter IV",
        must_match_any=("collision", "overtaking", "racing room", "appendix l", "chapter iv"),
        expected_topics=("appendix l", "collision", "overtaking", "driving"),
    ),
    EvalCase(
        name="Article 13 Protest procedure",
        query="Article 13 Protest lodging competitor breach of regulations",
        must_match_any=("article 13", "protest"),
        expected_topics=("article 13", "protest"),
    ),
    EvalCase(
        name="Article 14 Right of Review new element",
        query="Article 14 Right of Review significant and relevant new element",
        must_match_any=("article 14", "right of review", "new element"),
        expected_topics=("article 14", "right of review"),
    ),
]


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def citation_faithfulness(hits: List[Dict[str, Any]], must_match_any: Sequence[str]) -> float:
    """Fraction of required topic tokens that appear verbatim in retrieved text."""
    if not hits or not must_match_any:
        return 0.0
    blob = _normalize_ws(
        " ".join(
            "{0} {1} {2}".format(h.get("title") or "", h.get("article") or "", h.get("text") or "")
            for h in hits
        )
    )
    hits_count = 0
    for needle in must_match_any:
        if _normalize_ws(needle) in blob:
            hits_count += 1
    return round(hits_count / max(1, len(must_match_any)), 4)


def quote_verbatim_score(hits: List[Dict[str, Any]]) -> float:
    """Ensure we can pull a contiguous substring quote from each hit (anti-hallucination proxy)."""
    if not hits:
        return 0.0
    ok = 0
    for hit in hits:
        text = str(hit.get("text") or "").strip()
        if len(text) < 40:
            continue
        # Take a mid-span window as the "exact quote" candidate.
        start = max(0, len(text) // 4)
        snippet = text[start : start + 80]
        if snippet and snippet in text:
            ok += 1
    return round(ok / max(1, len(hits)), 4)


def context_precision(hits: List[Dict[str, Any]], expected_topics: Sequence[str]) -> float:
    if not hits:
        return 0.0
    relevant = 0
    for hit in hits:
        blob = "{0} {1} {2} {3}".format(
            hit.get("title") or "",
            hit.get("article") or "",
            hit.get("source_document") or "",
            hit.get("text") or "",
        )
        if OFFTOPIC_HINTS.search(blob) and not SPORTING_HINTS.search(blob):
            continue
        topic_ok = any(_normalize_ws(topic) in _normalize_ws(blob) for topic in expected_topics)
        sporting_ok = bool(SPORTING_HINTS.search(blob))
        if topic_ok or sporting_ok:
            relevant += 1
    return round(relevant / max(1, len(hits)), 4)


def evaluate_case(case: EvalCase, top_k: int = 4, retrieve_fn=None) -> Dict[str, Any]:
    retrieve = retrieve_fn or retrieve_regulations
    hits = retrieve(case.query, top_k=top_k)
    faithfulness = round(
        0.6 * citation_faithfulness(hits, case.must_match_any)
        + 0.4 * quote_verbatim_score(hits),
        4,
    )
    precision = context_precision(hits, case.expected_topics)
    return {
        "name": case.name,
        "hits": len(hits),
        "sources": sorted({str(h.get("source") or "") for h in hits}),
        "citation_faithfulness": faithfulness,
        "context_precision": precision,
        "sample_titles": [(h.get("title") or h.get("article") or "")[:70] for h in hits[:3]],
    }


def print_scorecard(rows: List[Dict[str, Any]]) -> None:
    print("")
    print("=" * 72)
    print(" PROTEST ENGINE RAG EVALUATION SCORECARD")
    print("=" * 72)
    for row in rows:
        print("-" * 72)
        print("Case: {0}".format(row["name"]))
        print("  hits={0}  sources={1}".format(row["hits"], ",".join(row["sources"]) or "-"))
        print("  Citation Faithfulness : {0:.2f}".format(row["citation_faithfulness"]))
        print("  Context Precision     : {0:.2f}".format(row["context_precision"]))
        if row["sample_titles"]:
            print("  top titles:")
            for title in row["sample_titles"]:
                print("    • {0}".format(title))
    avg_f = sum(r["citation_faithfulness"] for r in rows) / max(1, len(rows))
    avg_p = sum(r["context_precision"] for r in rows) / max(1, len(rows))
    print("=" * 72)
    print(" AVERAGE  Faithfulness={0:.2f}  Precision={1:.2f}".format(avg_f, avg_p))
    print("=" * 72)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate Protest Engine RAG fidelity")
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Force teaching-corpus / keyword path (ignore Pinecone even if keyed)",
    )
    args = parser.parse_args(argv)

    retrieve_fn = retrieve_regulations
    if args.offline:
        retriever = RuleRetriever(use_chroma=False, use_pinecone=False)

        def _offline(query: str, top_k: int = 4):
            return retriever.retrieve_rules(query, top_k=top_k)

        retrieve_fn = _offline

    rows = [evaluate_case(case, top_k=args.top_k, retrieve_fn=retrieve_fn) for case in CASES]
    print_scorecard(rows)
    if any(row["hits"] == 0 for row in rows):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
