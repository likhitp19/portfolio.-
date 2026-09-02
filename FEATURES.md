# Features — Apex F1 Suite

Inventory of **what is actually built** in this repo. Architecture and phase history live in [ARCHITECTURE.md](./ARCHITECTURE.md) and [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md). How to score the commercial agent: [EVALUATION.md](./EVALUATION.md).

**Product:** a dark **Formula 1 management console** with two desks on one FastAPI contract (`year`, `meeting_key`, `session_key`):

| Desk | Audience | What it does |
| --- | --- | --- |
| **Apex Analytics** (commercial) | Business / commercial | Constructor economics, driver ROI, cited USD facts, Executive Co-Pilot |
| **Regulatory Desk** (protest engine) | Technical / legal simulation | Incident clip → OpenF1 context + FIA RAG → Mercedes-AMG **Protest Dossier** |

This is **not** a live-timing app and **not** an official FIA filing tool.

Canonical UI brand: **Apex F1 Suite**. Older docs said “Paddock Ledger”; treat that as the same product.

---

## 1. Surfaces (routes)

| Route | Feature |
| --- | --- |
| `/` | **Portfolio home** — hero, about, selected projects, contact (editorial gold/emerald theme) |
| `/about` | Extended profile, philosophy, featured work |
| `/projects` | Full projects hub (same cards as home) |
| `/projects/apex-f1` | Apex F1 dual-lens case study |
| `/projects/piglow-led` | PiGlow LED Orchestra — coming soon placeholder |
| `/season/[year]` | Season ledger + Co-Pilot (Apex F1 product UI) |
| `/season/[year]/meeting/[meetingKey]` | Same desk scoped to one GP — changing circuit **re-fetches** `/api/dashboard` |
| `/steward` | Regulatory Desk: Spa demo clip, pipeline stepper, Protest Dossier |
| `/about` | Profile page (Likhit P.) with contact + photos |

**Shell:** sticky `SuiteHeader` switches Manufacturer ROI / Driver Assets / Regulatory / About. Season + All Circuits controls live under `/season/*` only.

Default season is **2026**. The year dropdown still covers a rolling window (≥10 seasons, e.g. 2017–2026). Selecting **2025** in the control maps to 2026.

---

## 2. Commercial desk — Manufacturer ROI

**Mounted when** `?tab=manufacturer` (default).

| Feature | What the user sees | Source of truth |
| --- | --- | --- |
| **Financial Telemetry KPIs** | Total grid valuation; avg budget-cap spend vs $135M FIA cap; Market Inefficiency Index (CPP coefficient of variation → TIGHT / ELEVATED / HIGH); Constructor Yield Leader + share of grid points | OpenF1/Jolpica constructor points + fact-store USD |
| **Constructor book** | Position, team logo, constructor yield (pts), valuation, cap, USD/pt, race wins, wins/GP. HoverCard cites source URL + retrieved date | Constructor championship (never a relabeled driver table). Wins from Jolpica WCC `wins` + paginated race results (sprints not counted) |
| **Cost-per-point chart** | Bar chart, team codes, efficiency bands vs grid average, average reference line. YTD is live; LTM/PROJ badges are labels only | `budget_cap_usd / constructor_points` |
| **Constructor era timeline** | Line chart 2014→now with Turbo-Hybrid / Ground Effect / Active Aero eras; click a year for “what changed” copy | `/api/analytics/constructor-timeline` (Jolpica + constructor lineage) |
| **Constructor yield over the season** | Points after each GP for constructors | Dashboard `constructor_progression` |

**Honesty rules:** constructor points come from constructor championship data. Commercial USD is **cited** (Estimate / Official / Conflict badges). Dashboard GET **never** calls Tavily.

---

## 3. Commercial desk — Driver Assets

**Mounted when** `?tab=driver`.

| Feature | What the user sees | Source of truth |
| --- | --- | --- |
| **Top-5 ROI cards** | Official F1 DAM headshots (2026→2025→2024 fallback, then initials), P-badge, S/A/B ROI tier, championship XP bar, points, salary, **FER** = salary / points | Championship drivers + fact-store salaries |
| **Teammate delta matrix** | Scatter: dominant points-share % vs average qualifying pace delta (ms). Quadrants: balanced / watch / high asset risk. Constructor logos | `/api/analytics/teammate-delta` |
| **Driver title chase** | Top-five points progression, circuit by circuit | Dashboard `progression` |

---

## 4. Commercial desk — Executive Co-Pilot

Lives **below** the analytics on every season / meeting page. Default starter: *Who is projected to win the Championship this year, and what does the data say?* (“This year” = **2026**.)

| Feature | Status |
| --- | --- |
| Multi-turn chat with `thread_id` | Shipped (`POST /api/chat`, `GET /api/chat/{thread_id}`) |
| SSE handoffs | Shipped (`POST /api/chat/stream`) — Generalist → Data Analyst ⇄ tools → Strategic Analyst → Technical Manager |
| Layered answer | Executive TL;DR, predicted winner + win %, key drivers, contender cards (headshots), in-depth report (markdown tables), follow-up chips |
| Contender yield chart | Bar chart parsed from answer tables (when ≥2 numeric series) |
| Server-owned **trace** | Routing, execution phases, API calls, pipelines, assumptions, missing inputs. UI never invents `trace` |
| Year from the **query** | Named year, or “this year/season” → 2026, else the page year |

### Agent intents (commercial graph)

| Intent | Capability |
| --- | --- |
| `championship_projection` | Implemented — live OpenF1/Jolpica standings, remaining-race math, DAM portraits |
| `constructor_finance` | Implemented — CPP, named-team compare, midfield slice (upside language is labeled inference) |
| `driver_roi` | Implemented — FER rank; nearest-year salary fallback labeled estimate |
| `regulatory_knowledge` | Implemented — **zero** OpenF1/Tavily calls |
| `historical_out_of_coverage` | Implemented — abstain (e.g. 1998 telemetry); **empty** `api_calls` |
| `research` | Implemented — Tavily when asked to look up online; sandbox notice if search 403s |
| `chitchat` | Implemented — no tools |
| `meeting_insights` / `comparative_standings` / `telemetry_compare` | Partial — calendar/results tools; no invented lap deltas |
| `teammate_h2h` | Intent only — gap in trace (quali/race H2H aggregation not in the tool plan) |
| `stint_strategy` | Intent only — gap; no `get_stints` |
| `position_gain` | Intent only — gap; no ranked grid join |

Scorecard and queries: [EVALUATION.md](./EVALUATION.md) + [`eval/catalog.json`](./eval/catalog.json).

---

## 5. Regulatory Desk — Protest Engine

Route `/steward`. Separate LangGraph from the commercial Co-Pilot.

| Feature | Status |
| --- | --- |
| **Spa Turn 5 auto-demo** | On load, plays `/testf1incident1.mp4` and runs the pipeline (2024 Spa, cars 44 & 63, lap 1) |
| **Custom incident upload** | Dropzone for MP4 / image; year, circuit, incident hint |
| **Pipeline stepper** | Vision (Qwen-VL) → OpenF1 telemetry & radio → Pinecone FIA rules → DeepSeek dossier. Reasoning wait shows elapsed time |
| **Protest Dossier** | Filing type (Article 13 Protest / Article 14 Right of Review), filing team (Mercedes-AMG Petronas), competitor, primary claim, **verbatim** citation cards (quote + source + page), evidence checklist (Present / Pending Phase 2 / Insufficient), success probability bar, legal-risk notes, next step |
| **Coarse OpenF1 traces** | Speed lines per involved car; degraded copy when telemetry is coarse |
| **JSON analyze** | `POST /api/steward/analyze_clip` |
| **Multipart upload** | `POST /api/steward/analyze_clip/upload` (inline vision cap 8 MB) |
| **SSE stages** | `POST /api/steward/analyze_clip/stream` |
| **HF telemetry contract** | `POST /api/steward/phase2/telemetry` returns `PHASE2_NOT_IMPLEMENTED` (schema only) |

Without `OPENROUTER_API_KEY`, vision/reason degrade to hint + OpenF1 + heuristic dossier. Without `PINECONE_API_KEY`, RAG uses teaching Markdown / keyword (CI-safe).

**Disclaimer (always shown):** simulated Team Principal dossier for a portfolio demo — not an official FIA Protest or Steward Decision.

---

## 6. About

`/about` — name, title, tagline, mailto / tel, two lifestyle photos. Not wired to APIs.

---

## 7. Backend API map

Health: `GET /health` → `{ status, facts_backend, facts_count }`.

### Dashboard & facts

| Method | Path | Feature |
| --- | --- | --- |
| GET | `/api/seasons` | Rolling year list |
| GET | `/api/meetings` | Circuits for a year |
| GET | `/api/championship/drivers` | Driver standings + FER |
| GET | `/api/championship/constructors` | Constructor standings + commercial join |
| GET | `/api/championship/summary` | Leader, gap, races, fastest lap, DNFs, top-3 |
| GET | `/api/standings/progression` | Driver points by GP |
| GET | `/api/dashboard` | Aggregate payload (cached ~15 min per year/meeting). Boot preload 2024/2025/2026 |
| GET | `/api/analytics/constructor-timeline` | Multi-era constructor points |
| GET | `/api/analytics/teammate-delta` | Teammate share vs quali delta |
| GET | `/api/facts/commercial` | Fact-store dump for a year |
| POST | `/api/facts/refresh` | Search → store (not used on dashboard GET) |

### Chat

| Method | Path | Feature |
| --- | --- | --- |
| POST | `/api/chat` | Full graph invoke |
| POST | `/api/chat/stream` | SSE `handoff` + `result` |
| GET | `/api/chat/{thread_id}` | Saved snapshot |

### Steward

| Method | Path | Feature |
| --- | --- | --- |
| POST | `/api/steward/analyze_clip` | JSON clip URL / hint / live_feed |
| POST | `/api/steward/analyze_clip/upload` | File upload |
| POST | `/api/steward/analyze_clip/stream` | SSE pipeline stages |
| POST | `/api/steward/phase2/telemetry` | Stub contract |

**Live lock:** OpenF1 401 during a session → `F1_LIVE_LOCK`. Never `session_key=latest`. OpenF1 404 → `[]`. ~3 req/s unauthenticated.

---

## 8. Data & integrations

| Concern | Implementation |
| --- | --- |
| Sporting 2023+ | OpenF1 v1 — meetings, sessions, championship, results, laps, car_data, location, race_control, team_radio |
| Older seasons / wins | Jolpica (Ergast) |
| Commercial USD | Cited **fact store** (Supabase when configured, else SQLite + seed). Frozen for completed years. See [FACTS.md](./FACTS.md) |
| Optional web search | Tavily (`search_commercial`) — only when the researcher graph runs |
| FIA legal RAG | Pinecone Serverless (PyMuPDF + header splitter ingest) with BM25 hybrid; Markdown fallback |
| Commercial LLM | DeepSeek (or OpenAI-shaped fallback) |
| Steward vision / counsel | OpenRouter: Qwen2.5-VL + DeepSeek-R1 |
| Driver / team art | F1 Cloudinary DAM via `frontend/lib/media.ts` |

---

## 9. Platform & ops

| Feature | Status |
| --- | --- |
| Next.js App Router + Tailwind + shadcn + Recharts | Shipped |
| FastAPI + LangGraph | Shipped |
| CORS for Vercel (`*.vercel.app` regex + explicit origins) | Shipped |
| Production split: Vercel UI + Railway API | See [DEPLOY.md](./DEPLOY.md) |
| Dashboard memory cache + `DASHBOARD_PRELOAD` | Shipped |
| Pytest suite (dashboard, finance, routing, eval catalog, steward graph/RAG, analytics) | Shipped; default path does not bill Pinecone/OpenRouter |

---

## 10. Built in code but not on the current happy path

These exist in the repo; they are **not** the live interview flow.

| Piece | Notes |
| --- | --- |
| `OverallSummary` | Championship KPIs + insight grid — component exists, **not mounted** on `DashboardView` |
| `InsightChips` / `insightChips()` | FER / CPP / cost-cap starter chips — **not** wired into `ChatPanel` (championship starter + follow-ups are) |
| `TraceInspector` | Alternate trace UI — Co-Pilot uses `AgentTracePanel` |
| High-frequency (10–100 Hz) telemetry ingest | Contract only; evidence items stay `pending_phase2` |
| Chat Tests 4–6 sporting math | Intent + honest gap, not computed pipelines |

---

## 11. Code map (feature → files)

| Feature | Primary files |
| --- | --- |
| Suite nav / desks | `frontend/components/layout/SuiteHeader.tsx` |
| Season + circuit | `TopNav.tsx`, `SeasonShell.tsx`, `app/season/**` |
| Manufacturer ROI | `ManufacturerDashboard.tsx`, `ManufacturerStandings.tsx`, `CostPerPointChart.tsx`, `ConstructorEraTimeline.tsx` |
| Driver Assets | `DriverCard.tsx`, `TeammateDeltaMatrix.tsx`, `PointsProgressionChart.tsx` |
| Co-Pilot | `ChatPanel.tsx`, `CopilotAnswer.tsx`, `ContenderCards.tsx`, `AgentTracePanel.tsx` |
| Protest UI | `app/steward/page.tsx`, `ProtestDossierPanel.tsx` |
| Dashboard API | `backend/app/routers/dashboard.py`, `services/dashboard.py` |
| Analytics API | `backend/app/services/analytics.py` |
| Commercial agents | `backend/app/agents/graph.py`, `planning.py`, `nodes/*` |
| Protest agents | `backend/app/agents/steward_graph.py`, `tools/openf1.py` |
| RAG / ingest | `services/rag_service.py`, `scripts/ingest_pdfs.py` |
| Facts | `services/fact_store.py`, `FACTS.md` |

---

## 12. Formulae (must match UI and eval)

| Metric | Formula | Split |
| --- | --- | --- |
| Cost-per-point | `budget_cap_usd / constructor_points` | Cap = store; points = OpenF1/Jolpica |
| FER | `salary_usd / driver_points` | Salary = store estimate; points = championship |
| Wins / GP | season race wins / completed grands prix | Jolpica; not sprint sessions |
| Positions gained | `grid − finish` | **Not** implemented in chat |

Division by zero → do not rank; say points were 0.
