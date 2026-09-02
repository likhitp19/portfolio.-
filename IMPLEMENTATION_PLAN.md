# Implementation plan — Apex F1 Suite

Aligned with [README.md](./README.md), [FEATURES.md](./FEATURES.md), and [ARCHITECTURE.md](./ARCHITECTURE.md).

Shipped feature inventory (what exists today): [FEATURES.md](./FEATURES.md).

Protest Phases 1–3 and commercial A1–A6 are complete. Remaining work is **additive** (e.g. high-frequency telemetry) and must not reopen shipped graphs unless fixing regressions.

---

## Active product focus

| Phase | Name | Status |
| --- | --- | --- |
| **Phase 1** | Pinecone RAG Setup & PDF Ingestion | **Done** (153 vectors upserted live) |
| **Phase 2** | LangGraph Updates (OpenF1 & Reasoning) | **Done** (live Spa smoke passed) |
| **Phase 3** | Next.js Protest Dossier UI | **Done** |

**Prior commercial desk (Phases A1–A6):** complete. Do not reopen unless fixing regressions. Protest work is **additive** (`steward_graph` is separate from the commercial chat graph).

**Ship:** Railway (API) + Vercel (Next.js). Sporting live-lock: `F1_LIVE_LOCK`. **No chronological race timeline.**

**Future (post Phase 3):** high-frequency micro-telemetry ingest (10–100 Hz) to flip `pending_phase2` evidence — documented in [ARCHITECTURE.md](./ARCHITECTURE.md) only until scheduled. Do not confuse that future work with **Phase 2** below (LangGraph / OpenF1).

---

## Dependency graph

```
Phase 1: FIA PDFs → PyMuPDF → MarkdownHeaderTextSplitter → Pinecone
    → Phase 2: steward_graph (OpenF1 race_control/team_radio + verbatim counsel)
        → Phase 3: /steward Mercedes-AMG Protest Dossier UI
```

---

## Phase 1 — Pinecone RAG Setup & PDF Ingestion

**Goal:** Official FIA Sporting Regulations PDFs become citation-ready vectors with page metadata.

**Git commit when done:** ingest script, Pinecone upsert path, RAG retrieve with page + source metadata, offline/CI fallback.

### Scope

- [x] Create `backend/scripts/ingest_pdfs.py` using **PyMuPDF** (`fitz`) to extract text from PDFs in `backend/app/data/pdfs/` (brief: `data/pdfs/`).
- [x] Implement **`MarkdownHeaderTextSplitter`** chunking (and/or recursive split on Article / Chapter) so legal clauses stay intact — **no** fixed-size character windows.
- [x] Upsert to **Pinecone** (Serverless Free Tier) with metadata that includes **`page_number`** and **`source_document`** (also carry `article` / `source` as needed for retrieval):

```json
{
  "source": "filename.pdf",
  "source_document": "filename.pdf",
  "page_number": 42,
  "article": "Article 14"
}
```

- [x] Wire `backend/app/services/rag_service.py` to query Pinecone (hybrid semantic + BM25 where available).
- [x] If `PINECONE_API_KEY` is empty: fall back to teaching Markdown / local keyword so pytest never bills Pinecone.
- [x] Update `requirements.txt` (`pinecone` / `pinecone-client`, `PyMuPDF`, `langchain` / `langchain-text-splitters`).
- [ ] Ask operator for Pinecone API key before live upsert; never commit secrets.

### Exit criteria

- Ingest run produces chunks that retain `page_number` + `source_document`.
- Retrieve returns citation-ready chunks for queries like “Causing a collision” / “Article 14”.
- Default pytest path makes no Pinecone network calls.

**Stop. Commit Phase 1. Await approval before Phase 2 code.**

---

## Phase 2 — LangGraph Updates (OpenF1 & Reasoning)

**Goal:** Context pack + counsel node emit a honest **ProtestDossier** with verbatim legal cites.

**Git commit when done:** OpenF1 tools + graph context gathering, strict counsel prompt, `ProtestDossier` schema with citation objects and Phase-2-bridge evidence list.

### Scope

- [x] Integrate **`/v1/race_control`** and **`/v1/team_radio`** into OpenF1 tools (`backend/app/tools/openf1.py`; also `/v1/car_data`, `/v1/location` as already required for telemetry).
- [x] Before `verdict_reasoning_node`, gather an OpenF1 context pack; degrade gracefully on empty / 401 / `F1_LIVE_LOCK`.
- [x] Update **`verdict_reasoning_node`** system prompt — **MUST**:
  - Extract **EXACT verbatim quotes** from RAG context (no paraphrasing).
  - Include **`page_number`** and **`source_document`** from chunk metadata on each citation.
  - Output **ProtestDossier** JSON with **`required_telemetry_evidence`** when OpenF1 data is coarse / missing micro-telemetry (e.g. Turn 5 steering angle).
- [x] `regulatory_violations` shape:

```json
{
  "article_name": "string",
  "exact_quote": "string",
  "page_number": 0,
  "source_document": "string"
}
```

- [x] `success_probability`: Low when micro-telemetry items are pending.
- [x] Stub `POST /api/steward/phase2/telemetry` contract only (future HF ingest — not this phase’s implementation).

### Exit criteria

- Graph context includes race control and/or team radio when OpenF1 returns data.
- Dossier normalize / heuristic path always emits citation objects with quote + page + source fields.
- Coarse telemetry never claims proven apex understeer without pending evidence items.
- Default pytest: no OpenRouter / Pinecone billing.

**Stop. Commit Phase 2. Await approval before Phase 3 code.**

---

## Phase 3 — Next.js Protest Dossier UI

**Goal:** Render the Phase 1 assessment as a formal constructor filing UI.

**Git commit when done:** `/steward` Mercedes-AMG dossier panel wired to `protest_dossier`.

### Scope

- [x] Build the **“Mercedes-AMG Petronas FIA Protest Dossier”** UI at `/steward`.
- [x] Render **RegulatoryCitation** cards: `article_name`, blockquote **`exact_quote`**, badge with **`source_document`** + **`page_number`**.
- [x] Render **`required_telemetry_evidence`** checklist with status badges:
  - **Present** (green)
  - **Pending Phase 2** (gold / yellow) — means *future HF telemetry ingest*, not Implementation Phase 2
  - **Insufficient** (red)
- [x] Display `success_probability` (Low / Medium / High) via progress bar or colored indicator.
- [x] Keep `frontend/lib/steward.ts` types aligned with backend `ProtestDossier` / `RegulatoryCitation`.

### Exit criteria

- Demo: analyze incident → dossier shows quoted regulation lines, page badges, and evidence checklist.
- Empty dossier state is formal (header present), not a blank card.

**Stop. Commit Phase 3.**

---

## Historical commercial desk (complete — do not reopen)

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

## Feature inventory vs this plan

[FEATURES.md](./FEATURES.md) is the live map of desks, APIs, and agent intents. This file is the **phase history**. Do not treat unchecked historical commercial work as unfinished — A1–A6 and Protest 1–3 are complete.

---

## Out of scope (all current work)

- Issuing a real FIA Protest or Steward Decision.
- Claiming Pinecone citations are audited legal advice.
- Live betting / brokerage execution.
- Reintroducing a chronological event timeline on the commercial desk.
- Treating whole-lap OpenF1 samples as apex-window proof of understeer/contact.
- Implementing high-frequency telemetry ingest (10–100 Hz) until it is scheduled as its own phase. `POST /api/steward/phase2/telemetry` remains a schema stub.
