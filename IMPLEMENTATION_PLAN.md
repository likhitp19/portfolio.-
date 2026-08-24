# Implementation plan — F1 Business Intelligence

Aligned with [README.md](./README.md) and [ARCHITECTURE.md](./ARCHITECTURE.md).

**Do not start a phase until the previous phase’s exit criteria are met and the phase commit is approved.**

**Target:** business F1 console (valuations, ROI, insights) + LangGraph trace. **≥10 seasons** in the nav. Sporting live-lock: **`F1_LIVE_LOCK`**. Facts: search → **Supabase** (SQLite fallback). Ship: **Railway** (API + Next.js/React). **No timeline.**

**Status:** Phase 5 **complete**. Interview layout is ledger then Co-Pilot; championship starter + SSE handoffs (not generic chips).

Each phase below is a **discrete Git commit**. Do not mix manufacturer finance into Phase 1, or LangGraph into Phase 3.

Commercial dollars are **search → store → UI**. Phase 1 does not call Tavily. Phase 2 introduces the store + refresh job. Phase 3 reuses the same store for salaries.

---

## Phase 1 — Setup & reactive state

**Git commit when done:** setup, Shadcn shell, All Circuits routing, dashboard re-fetch contract, `F1_LIVE_LOCK` plumbing (no finance widgets yet).

### Scope

- [x] Next.js App Router + Tailwind + **Shadcn** primitives used in the shell: `Card`, `Tabs`, `Badge`, `Alert`, `Separator` (HoverCard may wait until Phase 3).
- [x] Dark theme on `:root`, `color-scheme: dark` on `html` and native selects.
- [x] TopNav circuit label: **All Circuits** (never “All Meetings”).
- [x] Season `<select>` → `/season/{year}` and **clear** circuit view.
- [x] Circuit `<select>` → `/season/{year}/meeting/{id}` and `loadDashboard(year, id)` so **every** widget uses the new `/api/dashboard?meeting_key=` payload.
- [x] Remount/key strategy so the previous GP cannot linger.
- [x] OpenF1 historical policy: completed races only; ignore `session_key=latest`; 404 → empty.
- [x] HTTP 503 + `detail.code = "F1_LIVE_LOCK"` surfaced in `Alert` (code + wait-and-refresh copy).
- [x] Same-origin `/api` rewrite to `http://127.0.0.1:8000`.
- [x] **10-year** season window; Jolpica calendar if OpenF1 has no meetings; Supabase env placeholders (no Tavily on GET).
- [x] Tab **hosts** (Manufacturer / Driver / Overall Summary); finance charts still Phase 2.
- [x] Overall Summary KPIs + insights; **no** timeline.

### Exit criteria

- Switching All Circuits ↔ a completed GP changes the URL and the dashboard JSON `meeting_key`.
- `F1_LIVE_LOCK` is visible if OpenF1 returns live-session 401 (or in a fixture test).
- `GET /health` 200; dark shell loads.

**Stop. Commit Phase 1. Do not start Phase 2 without approval.**

---

## Phase 2 — The business dashboard (Manufacturer)

**Git commit when done:** constructor economics only.

### Scope

- [x] Manufacturer tab consumes **constructor** points (`championship_teams` / constructor adapter). **Ban** driver-point rows.
- [x] **Fact store** (SQLite + optional committed `commercial_facts.seed.json`): schema in ARCHITECTURE §2.2.
- [x] **Search client** (Tavily): `search_commercial` used **only** by `POST /api/facts/refresh` / CLI job — **never** inside `GET /api/dashboard`.
- [x] Accuracy: domain allowlist, sanity bounds, conflict if sources differ >20%, freeze completed years, citations on every row.
- [x] Join store → team **valuation**, **budget cap**, **cost-per-point** = cap / constructor points (null if 0 points).
- [x] **Wins** and **average wins per manufacturer** from completed race results (OpenF1).
- [x] UI: Shadcn `Table` + `Badge` (Estimate / Official / Conflict) + `HoverCard` with **source URL + retrieved_at**.
- [x] Recharts **`CostPerPointChart`**: bar per constructor; tooltip includes citation year.
- [x] Callout card for lowest CPP with points &gt; 0.
- [x] Tests: dashboard does not invoke search; frozen year not overwritten without `force`; constructor table ≠ driver standings; CPP formula.

### Exit criteria

- Business analyst can compare efficiency vs valuation without opening the Driver tab.
- No timeline. No FIFA cards yet.

**Stop. Commit Phase 2.**

---

## Phase 3 — Gamification (Driver)

**Git commit when done:** FIFA-style ROI cards + top-5 chart.

### Scope

- [x] Driver payload sliced to **top 5**; progression `series.length == 5`.
- [x] Salaries from the **same fact store** (search-backed, cited); **FER** = `salary_usd / points` (null if 0 points).
- [x] **`DriverCard`**: Shadcn `Card`, `Avatar` placeholder, `Badge` position, salary, points, FER + ROI band, `HoverCard` with salary **citation**.
- [x] **`DriverRoiGrid`** on the Driver tab (not a dense 20-row table as the hero).
- [x] **`PointsProgressionChart`**: five `Line` series; premium tooltip (circuit, pts).
- [x] Tests: five series; FER formula; cards ordered by championship position; missing salary → defaulted badge, not a guessed LLM number.

### Exit criteria

- Demo: top 5 cards + chart; “who is expensive per point?” is obvious in five seconds.

**Stop. Commit Phase 3.**

---

## Phase 4 — Agentic backend (LangGraph)

**Git commit when done:** FastAPI graph with three roles; finance-aware tools.

### Scope

- [x] `F1DashboardState` and topology: Generalist → Data Analyst **or Researcher** ⇄ tools → Technical Manager.
- [x] Generalist: bind `season_year` / `meeting_key`; **no** OpenF1; **no** timeline intent; route constructor_finance / driver_roi / standings / insights / research / chitchat.
- [x] Data Analyst: autonomous plan; loop until `needs_more_data` is false; store tool `get_finance_estimates` (no live search).
- [x] **Researcher:** `search_commercial` (Tavily) then write-through to the fact store; citations only, no invented USD.
- [x] Technical Manager: `routing`, `reasoning_path`, `api_calls`, `pipelines` (`finance_fact_store`, `search_commercial`). Never fetch.
- [x] Throttle, cache, 404, `F1_LIVE_LOCK` unchanged.
- [x] Tests: greeting → empty `api_calls`; cost-per-point → store not search; “look up online” → researcher + `search_commercial`.

### Exit criteria

- OpenAPI includes dashboard + `POST /api/chat`. Trace proves branching for commercial vs sporting prompts.

**Stop. Commit Phase 4.**

---

## Phase 5 — Chat UI & trace

**Git commit when done:** frontend wired to graph; demo-ready.

### Scope

- [x] Chat split: messages + `TraceInspector`; `thread_id` in client state; context `year` + `meeting_key`.
- [x] Insight chips **above** input (cost-per-point, driver FER, constructor after this circuit, DNF/operational risk, look up online). Chip click = `sendChat` with chip text + context.
- [x] Never invent `trace`; show server trace on partial errors if present.
- [x] Overall Summary insights grid complete (fastest lap, DNFs, top-3); still **no** timeline.
- [x] Demo script:
  1. 2025, All Circuits — Manufacturer CPP chart, Driver cards, insights.
  2. Select a circuit — all widgets refresh (`meeting_key` in payload).
  3. Chip “best cost-per-point” — Analyst uses **fact store** (and OpenF1 points); `search_commercial` only if the store was empty.
  4. “What can you do?” — empty `api_calls`.
  5. If GP is on air — UI shows **`F1_LIVE_LOCK`**.

### Exit criteria

- Engineers see the trace; analysts see ROI language in the answer. Both share one circuit context.

**Stop. Commit Phase 5.**

---

## Out of scope (all phases)

- Live timing, paid OpenF1 live keys, streaming tokens, real brokerage/betting execution, audited club accounts, copyrighted driver photography (placeholders only unless licensed).
- Reintroducing a chronological event timeline.
- Driver points as the Manufacturer table.

---

## Phase dependency graph

```
Phase 1  Setup & state (All Circuits, Shadcn shell, F1_LIVE_LOCK)
    → Phase 2  Manufacturer business (search → store → CPP chart, wins)
        → Phase 3  Driver gamification (FIFA cards, FER from same store, top-5 chart)
            → Phase 4  LangGraph (Generalist, Analyst, Technical Manager)
                → Phase 5  Chat UI + trace + business chips
```

Phase 2–3 may ship UI against `/api/dashboard` fields added in those same phases. Phase 5 must not invent trace JSON on the client.

---

## Phase 6 — Evaluation contract (documentation + trace)

**Git commit when done:** eval spec, catalog, execution_trace, Tests 7–8 abstention.

### Scope

- [x] `EVALUATION.md` + `eval/catalog.json` (eight tests, four quality dimensions, API cleanliness).
- [x] Technical Manager emits `execution_trace`, `missing_inputs`, `assumptions` (joins, formulae, gaps).
- [x] Regulatory / pre-2023 telemetry questions take `generalist_direct` with **empty** `api_calls`.
- [x] Tests 4–6: intent recognized; explicit gap; no lap dumps.

### Exit criteria

A Technical Manager can score Tests 1–3 and 7–8 from the server trace without inferring hidden chain-of-thought.

**Stop. Commit Phase 6.**

---

## Backlog from live eval (do not mix into a Phase 6 commit unless fixing chat)

Observed when the UI season is 2024 but the **question names 2023**:

1. **Query year wins.** `"… from 2023 …"` must set tool `year=2023`. Dashboard `year=2024` is only a fallback.
2. **Investor / midfield is constructor finance**, not `comparative_standings`. Do not answer with first-vs-last championship snapshots or `list_meetings` / `list_sessions`.
3. **OpenF1 `championship_drivers?year=` can return 0 rows.** Resolve last race `session_key`, then Jolpica driver/constructor standings.
4. **Join failures must name keys** (salary `entity_key` vs `driver_number`), and `execution_trace` must not be empty.
5. Manufacturer chart copy: **Constructor points across the season** (not “circuits”).
6. After agent changes, **restart uvicorn**. A running API will keep serving the old graph.

Pytest: `backend/tests/test_user_eval_queries.py` uses the exact Desk questions with `year: 2024` in the POST body.
