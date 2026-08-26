# Implementation plan — Team Principal Protest & Review Engine

Aligned with [README.md](./README.md) and [ARCHITECTURE.md](./ARCHITECTURE.md).

**Do not start a phase until the previous phase’s exit criteria are met and the phase commit is approved.**

**Active product focus:** Phase 1 of the **Team Principal Protest & Review Engine** — PDF legal RAG (Pinecone), OpenF1 context gathering (`car_data`, `race_control`, `team_radio`), and a structured **Protest Dossier** UI.

**Prior commercial desk (Phases A1–A6 below):** complete. Do not reopen those commits unless fixing regressions. Protest work is **additive** and uses a separate LangGraph (`steward_graph`).

**Ship:** Railway (API) + Vercel (Next.js). Sporting live-lock: `F1_LIVE_LOCK`. **No chronological race timeline.**

---

## Dependency graph (active)

```
FIA PDFs → PyMuPDF / MarkdownHeaderTextSplitter → Pinecone (page metadata)
    → steward_graph (vision → OpenF1 context → RAG → ProtestDossier)
        → POST /api/steward/analyze_clip[+ /upload|/stream]
            → frontend/app/steward/page.tsx
```

Phase 2 (micro-telemetry ingest) is **documented only** until explicitly scheduled.

---

## Protest Phase 1 — Legal RAG & OpenF1 context

**Git commit when done:** PDF ingest pipeline, Pinecone index + metadata, OpenF1 `race_control` / `team_radio` in the graph, Protest Dossier citations with exact quotes + page numbers, dossier UI.

### 1.1 PDF ingestion & semantic legal chunking

- [ ] Official FIA PDFs live under `backend/app/data/pdfs/`.
- [ ] `backend/app/services/rag_service.py` (path map: brief `backend/services/…` → this file):
  - Extract text with **PyMuPDF** (`fitz`) and/or **`pymupdf4llm`**, preserving **page number** on every page.
  - Chunk with LangChain **`MarkdownHeaderTextSplitter`** and/or recursive separators (`\nArticle`, `\nChapter`, `\nAppendix`) — **no** fixed-size character splitter that bisects clauses.
  - Upsert to **Pinecone Serverless (Free Tier)** with metadata:

```json
{"source": "filename.pdf", "page_number": 42, "article": "Article 14"}
```

- [ ] Hybrid query path: semantic + BM25 (e.g. “Causing a collision”, “Article 14”).
- [ ] CI / offline: if `PINECONE_API_KEY` is empty, fall back to teaching Markdown / local keyword so pytest never bills Pinecone.

**Packages:** `pymupdf`, `pymupdf4llm` (optional), `langchain-text-splitters`, `pinecone` (or `pinecone-client`).

### 1.2 OpenF1 context gathering

Before the counsel / reasoning node:

- [ ] Resolve `session_key` (never `session_key=latest`).
- [ ] Fetch in parallel where possible:
  - `/v1/car_data`, `/v1/location`, `/v1/laps`
  - `/v1/race_control` — official warnings / investigation notes
  - `/v1/team_radio` — driver–pit audio / transcripts when available
- [ ] Format a structured **OpenF1 context pack** (telemetry summary + race-control messages + radio excerpts).
- [ ] Empty / 401 / `F1_LIVE_LOCK` → degrade; continue; mark evidence gaps in the dossier.

### 1.3 Protest Dossier schema & counsel node

- [ ] `regulatory_violations` is an array of objects:

```json
{
  "article_name": "string",
  "exact_quote": "string",
  "page_number": 0,
  "source_document": "string"
}
```

- [ ] Counsel prompt **STRICT DIRECTIVE:** extract the **EXACT verbatim quote** from retrieved chunk text; include `page_number` and `source` exactly as in chunk metadata; **do not paraphrase** rule text.
- [ ] Always populate `required_telemetry_evidence` when OpenF1 data is coarse / ambiguous (Phase 2 bridge).
- [ ] `success_probability`: Low when micro-telemetry is pending.

### 1.4 HTTP & UI

- [ ] `POST /api/steward/analyze_clip`, `/upload`, `/stream` return `protest_dossier`.
- [ ] Stub `POST /api/steward/phase2/telemetry` (schema contract only).
- [ ] `/steward`: Mercedes-AMG Petronas dossier panel; citation cards show quote + page + source; evidence checklist badges (`present` / `pending_phase2` / `insufficient`).

### 1.5 Tests

- [ ] PDF (or fixture) chunk retains `page_number` + `source` metadata.
- [ ] Retrieve query returns citation-ready chunks.
- [ ] Dossier normalize coerces violation objects; heuristic path still emits page-aware structure when LLM is offline.
- [ ] Missing OpenF1 → Low probability + pending Phase 2 items.
- [ ] No Pinecone / OpenRouter calls in default pytest.

### Exit criteria

- Demo: incident + live feed → dossier with **quoted** regulation lines and **page numbers**.
- OpenF1 pack includes race control and/or team radio when the API returns data.
- Coarse telemetry never becomes a confident “proven understeer” claim without Phase 2 items listed.

**Stop. Commit Protest Phase 1.**

---

## Protest Phase 2 — High-frequency telemetry (future)

**Not started.** Spec only in [ARCHITECTURE.md](./ARCHITECTURE.md) §6 and `Phase2TelemetryIngestRequest`.

- [ ] Ingest 10–100 Hz steering / brake / throttle / GPS channels.
- [ ] Re-score dossier: flip evidence `pending_phase2` → `present` / `insufficient`.
- [ ] Optional Article 14 “significant new element” framing when original steward pack lacked these traces.

---

## Historical commercial desk (complete — do not reopen)

These phases shipped the Apex Analytics ledger + Co-Pilot. Kept for audit only.

| Phase | Summary | Status |
| --- | --- | --- |
| A1 | Setup, Shadcn shell, All Circuits, `F1_LIVE_LOCK` | Complete |
| A2 | Manufacturer business (fact store, CPP, wins) | Complete |
| A3 | Driver ROI cards + top-5 progression | Complete |
| A4 | LangGraph commercial agents | Complete |
| A5 | Chat UI + SSE handoffs | Complete |
| A6 | Evaluation contract + abstention tests | Complete |

Commercial dollars remain **search → store → UI**. Dashboard GET never calls Tavily. Protest graph must not invent commercial USD.

---

## Out of scope (all current work)

- Issuing a real FIA Protest or Steward Decision.
- Claiming Pinecone citations are audited legal advice.
- Live betting / brokerage execution.
- Reintroducing a chronological event timeline on the commercial desk.
- Treating whole-lap OpenF1 samples as apex-window proof of understeer/contact.
