# Architecture — F1 Business Intelligence & Multi-Agent System

Contract aligned with [README.md](./README.md) and [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md).

**Product north star:** a console that a **team principal’s commercial staff** and a **performance engineer** can sit in front of together.

**Priorities:** (1) **≥10 seasons** + All Circuits reactivity; (2) constructor business metrics; (3) driver ROI cards; (4) insights, no timeline; (5) LangGraph trace; (6) facts in **Supabase**; (7) **Railway** + Next.js.

Sporting history: OpenF1 (2023+) and Jolpica/Ergast (older). Commercial: search → Supabase/SQLite.

There is **no Chronological Event Timeline**.

---

## 1. System context

```
┌──────────────────────┐  same-origin /api/*  ┌─────────────────────────┐    HTTPS     ┌─────────────┐
│ Next.js App Router   │ ◄──────────────────► │ FastAPI                 │ ◄──────────► │ OpenF1 v1   │
│ Shadcn + Recharts    │                      │ dashboard (no LLM)      │              └─────────────┘
└──────────┬───────────┘                      │ reads fact STORE only   │                    ▲
           │ chat + trace                     │         │               │                    │
           │                                  │         ▼               │    HTTPS     ┌─────┴───────┐
           │                                  │ SQLite/JSON fact store  │ ◄─────────── │ Search API  │
           │                                  │         ▲               │  refresh job │ (Tavily)    │
           │                                  │         │               │              └─────────────┘
           │                                  │ LangGraph (on miss /    │
           │                                  │ explicit research)      │
           │                                  │ Generalist              │
           │                                  │ Data Analyst ⇄ tools    │
           │                                  │ Technical Manager       │
           └──────────────────────────────────┴─────────────────────────┘
```

- Frontend never calls OpenF1 **or** the search API.
- **Dashboard GET** joins completed-race OpenF1 DTOs with the **local fact store**. It does **not** fire a web search per page view.
- **Refresh job / agent tool** `search_commercial` runs only on cache miss, admin refresh, or an explicit research question — then **upserts** the store.
- OpenF1 client: TTL cache, **~3 req/s**, **404 → `[]`**, 429 retry, **never `session_key=latest`**.
- Live-session global 401 → HTTP **503**, `detail.code = "F1_LIVE_LOCK"`.
- Technical Manager **only** compiles `F1DashboardState` → `AgentTrace`.

---

## 2. Domain model

| Concept | Source | UI |
| --- | --- | --- |
| **Meeting** | OpenF1 `meeting_key` | Circuit dropdown. **All Circuits** = no `meeting_key` |
| **Session** | Race (completed `date_end`) | Championship snapshot, insights, agent tools |
| **Constructor** | `championship_teams` | Manufacturer tab **points** |
| **Team finance** | Fact store (search-backed) | Valuation, published cap, cost-per-point |
| **Win tally** | Session results `position == 1` | Average / total wins per manufacturer |
| **Driver** | `championship_drivers` | Top 5 + F1 DAM portraits |
| **Driver finance** | Fact store (search-backed salary) | Financial efficiency rating |
| **Insights** | `session_result`, `laps` | Fastest lap, DNFs, top-3 finishes |

Canonical IDs: `year`, `meeting_key`, `session_key`, `driver_number`, `team_name`.

**Season overview:** `year` only. **Circuit view:** `year` + `meeting_key`. Dropdown change **navigates** and **re-fetches** the full dashboard payload.

### 2.1 Business formulas (must be implemented exactly)

All money in **USD**. Division by zero → `null` efficiency (UI: em dash + `Badge` “n/a”).

| Metric | Formula | Notes |
| --- | --- | --- |
| **Budget cap** | Fact store: FIA published cap for that season (search “FIA Formula 1 financial regulations cost cap {year}”) | Default fallback **$135,000,000** only if no cited row exists; `estimate_quality: "defaulted"` |
| **Team valuation** | Fact store: published enterprise-value / sale estimates for `{team} {year}` | Typical public range ~$700M–$4B. Prefer Sportico, Forbes, Reuters, Autosport. Labeled **Estimate** unless a completed sale is cited |
| **Cost-per-point** | `budget_cap_usd / constructor_points` | Lower is more efficient. OpenF1 supplies points only |
| **Wins (constructor)** | Count of race wins (`position == 1`) attributed to `team_name` in completed races in scope | Circuit filter uses that meeting only |
| **Avg wins / manufacturer** | `wins / max(race_count, 1)` | Shown as decimal (e.g. 0.45) |
| **Driver salary** | Fact store: `{driver} F1 salary {year}` from reputable motorsport press | **Estimate** unless the team published a figure |
| **Financial efficiency rating (FER)** | `salary_usd / championship_points` | Dollars per point. Lower = better ROI |
| **Sponsor / betting insight (narrative)** | Agent + copy only | Never present as odds or a recommendation to wager |

### 2.2 Commercial fact store and search (OpenF1 cannot do this)

OpenF1 does **not** expose team valuations, driver retainers, or sponsor rates. Those facts are gathered with a **search engine API** (default **Tavily**; interface `SearchClient.search(query, max_results)` so Brave/SerpAPI can replace it) and then **persisted**.

**Why persist:** a 2024 McLaren valuation or a 2023 cap figure barely moves. Re-searching on every `/api/dashboard` is slow, expensive, and more likely to pick up a bad snippet. Historical rows (`season_year` already complete) are **frozen**: updates require an explicit `--force` refresh, not an automatic overwrite.

**Store location:** SQLite `backend/data/commercial_facts.sqlite` (gitignored runtime) plus committed seed `backend/app/data/commercial_facts.seed.json`. With `SUPABASE_URL` and `SUPABASE_ANON_KEY` and table `public.commercial_facts`, the API hydrates from and writes to Supabase so Railway deploys keep valuations. DDL: `backend/app/data/commercial_facts.sql`. Operator guide: [FACTS.md](./FACTS.md).

**Row schema (logical):**

| Field | Purpose |
| --- | --- |
| `entity_type` | `constructor` \| `driver` \| `regulation` |
| `entity_key` | `team_name` or `driver_number` or `fia_cost_cap` |
| `season_year` | Championship year the figure applies to |
| `metric` | `valuation_usd` \| `salary_usd` \| `budget_cap_usd` |
| `value_usd` | Parsed number |
| `status` | `official` \| `estimate` \| `conflict` \| `defaulted` |
| `confidence` | 0–1 from source rank + parse quality |
| `source_url`, `source_title` | Citation for HoverCard |
| `snippet` | Short quoted context (not the full page) |
| `retrieved_at` | ISO timestamp |
| `frozen` | `true` for completed seasons |

**Accuracy rules (must implement):**

1. **Read path:** dashboard and chat `get_finance_estimates` **only hit the store**.
2. **Write path:** `search_commercial` builds a **constrained query** (entity + metric + year + “USD” / “cost cap”). Prefer domains: `fia.com`, `formula1.com`, `reuters.com`, `bbc.com`, `autosport.com`, `the-race.com`, `racefans.net`, `forbes.com`, `sportico.com`. Down-rank forums and social.
3. **Parse:** extract a single USD amount and the year. Reject values outside sanity bounds (valuation $200M–$6B; salary $0–$80M; cap $100M–$200M unless FIA restates).
4. **Corroborate:** if two preferred sources differ by **>20%**, store `status=conflict`, keep `value_usd` as the median, and expose `value_low` / `value_high` for the UI.
5. **No hallucinated numbers:** if search returns nothing usable, use a **documented default** and `status=defaulted` — never an LLM-invented dollar figure.
6. **Refresh:** completed years frozen; current year TTL default **7 days**. CLI: `python -m app.jobs.refresh_commercial_facts --year 2025`.
7. **PII/copyright:** store numbers + citations, not full article HTML or copyrighted headshots.

Unknown teams/drivers: mid-pack default + `defaulted` until search succeeds.

---

## 3. Frontend

### 3.1 Tree (target)

```
frontend/
  app/
    layout.tsx                       # dark :root, color-scheme
    page.tsx                         # redirect last completed season
    season/[year]/
      layout.tsx                     # AppShell + TopNav (keeps nav while page loads)
      page.tsx                       # All Circuits dashboard
      meeting/[meetingKey]/page.tsx  # same tabs, circuit-scoped payload
  components/
    layout/AppShell.tsx, TopNav.tsx
    dashboard/
      ChampionshipTabs.tsx          # Shadcn Tabs
      ManufacturerStandings.tsx      # constructor table + valuation badges
      CostPerPointChart.tsx          # Recharts BarChart
      ManufacturerWins.tsx           # avg wins
      DriverRoiGrid.tsx              # FIFA-style cards
      DriverCard.tsx                 # Card + Avatar + HoverCard
      PointsProgressionChart.tsx     # top 5 LineChart
      OverallSummary.tsx             # KPI Cards + insights grid
    chat/
      ChatPanel.tsx, MessageList.tsx, TraceInspector.tsx
  lib/api.ts, types.ts, formatMoney.ts
```

**Forbidden:** `EventTimeline`, `/api/events/timeline`.

### 3.2 Header, routing, reactivity

`TopNav` (Shadcn-adjacent native `<select>` with `color-scheme: dark`, or `Select` if already installed):

- Season change → `router.push(/season/{year})` — **clears** circuit.
- Circuit first option: label **All Circuits**, `value=""`.
- Circuit option: `circuit_short_name` / GP name, `value=meeting_key` → `/season/{year}/meeting/{id}`.

**Circuit reactivity (strict):**

1. URL contains `meeting_key` or not.
2. Page calls `loadDashboard(year, meetingKey?)` → `GET /api/dashboard`.
3. Manufacturer, Driver (cards + chart), Overall Summary **all** bind to that payload. Remount via `key={year-meetingKey}`.
4. Chat `sendChat` includes the same `year` and `meeting_key`.

Stale previous-GP numbers are a **P0 bug**.

Error **`F1_LIVE_LOCK`:** `Alert` (destructive) with monospaced `Error F1_LIVE_LOCK` and copy: wait until the session is over, then refresh. Do not prompt for a live API purchase.

### 3.3 Shadcn / aesthetics

| Component | Use |
| --- | --- |
| **Card** | Manufacturer table host, FIFA driver cards, KPI tiles, chat |
| **Tabs / TabsList / TabsTrigger** | Manufacturer · Driver · Overall Summary |
| **Badge** | “Estimate”, “Budget cap”, constructor position, FER “elite / poor ROI” bands |
| **HoverCard** | Citation: source title, URL, retrieved date, status (estimate / official / conflict range) |
| **Table** | Constructor standings (points, valuation, CPP, wins) |
| **Avatar** | Driver headshot **placeholder** (initials or generic silhouette — no scraped copyrighted photos required in Phase 3) |
| **Alert** | `F1_LIVE_LOCK` and load failures |
| **Separator / ScrollArea** | Chat + trace split |

Visual language: dark zinc/carbon, one accent (championship red or constructor colour if mapped), generous padding, tabular nums for USD and points.

### 3.4 Manufacturer tab (business view)

Layout (top → bottom):

1. **Constructor table** — columns: Pos, Manufacturer, Points, **Valuation** (compact USD, `Badge` Estimate), **Budget cap**, **Cost-per-point**, **Wins**, **Avg wins**.
2. **`CostPerPointChart`** — Recharts `BarChart`, X = team short name, Y = USD per point. Custom `Tooltip`: team, points, cap, CPP. Sort ascending (most efficient left) or keep championship order — **championship order** for alignment with the table; tooltip states efficiency rank.
3. Optional spark: callout `Card` for “most efficient constructor” (min CPP among teams with points > 0).

**Ban:** driver names or driver points as the primary manufacturer series.

### 3.5 Driver tab (gamified ROI)

1. **`DriverRoiGrid`** — up to **five** `DriverCard`s (championship order).
   - Header: official F1 DAM headshot (`driverHeadshotFallbacks`) + `Badge` P1–P5.
   - Body: name, team, **points**, **estimated salary**, **FER** (salary/points) as large number + `Badge` band (e.g. FER &lt; $200k/pt “High ROI”).
   - `HoverCard`: FER formula **and** salary citation from the fact store.
2. **`PointsProgressionChart`** — **exactly five** Recharts `Line` series. X = circuit short name (completed races); Y = cumulative points. Tooltip: driver, pts after that GP.

### 3.6 Overall Summary tab

- Row of KPI `Card`s: Championship **leader**, **leader points**, **gap to P2**, **races completed**.
- **Insights** grid (same visual weight, not a timeline): **fastest lap** (driver + time), **total DNFs**, **top-3 finishes** (driver + count).
- Optional one-line commercial gloss (static copy): DNFs as reliability/cost risk; podiums as sponsor exposure. Not a betting line.

### 3.7 Chat (Phase 5)

Interview layout: **dashboard (numbers + charts) above**, **Executive Co-Pilot below**. Default year **2026**.

`POST /api/chat` → `{ thread_id, answer, layers, trace }`. `POST /api/chat/stream` is SSE (`handoff` then `result`). **Never** invent `trace` on the client.

Starter (no generic chips): “Who is projected to win the Championship this year, and what does the data say?” Intent `championship_projection` loads sessions, standings, classifications, laps, and drivers; Strategic Analyst writes the TL;DR + tables.

`AgentTracePanel` (collapsible): `agent_handoffs`, `reasoning_path`, `api_calls` (path, status, `duration_ms`). Store reads → `finance_fact_store`. Live Tavily → `search_commercial`. Never label a stored fact as OpenF1.

---

## 4. FastAPI routes

Dashboard routes **must not** call the LLM.

### 4.1 Platform

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness |
| `GET` | `/docs` | OpenAPI |

### 4.2 Dashboard

| Method | Path | Query | Response |
| --- | --- | --- | --- |
| `GET` | `/api/seasons` | — | `{ years }` (2023+) |
| `GET` | `/api/meetings` | `year` | Circuits for TopNav |
| `GET` | `/api/championship/constructors` | `year`, optional `meeting_key` | Constructor points **plus** valuation, cap, CPP, wins, avg_wins |
| `GET` | `/api/championship/drivers` | same | Top **5** + salary + FER |
| `GET` | `/api/championship/summary` | same | Leader KPIs + insights |
| `GET` | `/api/standings/progression` | `year` | Top **5** series |
| `GET` | `/api/dashboard` | `year`, optional `meeting_key` | Aggregate for the UI (OpenF1 + **store**, no live search) |
| `GET` | `/api/facts/commercial` | `year` | Audit: stored rows + citations (no search) |
| `POST` | `/api/facts/refresh` | `{ year, force? }` | Runs search upsert (ops / Phase 2 job; protect in prod) |

**Removed:** `GET /api/events/timeline`.

OpenF1 mapping:

| Concern | Resources |
| --- | --- |
| Nav | `/v1/meetings` |
| Constructors | `/v1/championship_teams` (fallback: constructor scoring sums, **not** a driver table) |
| Drivers / progression | `/v1/championship_drivers` after **completed** races |
| Insights / wins | `/v1/session_result`, `/v1/laps` |

404 “No results found” → `[]`. Incomplete/future races excluded.

### 4.3 Error contract

```json
{
  "detail": {
    "code": "F1_LIVE_LOCK",
    "message": "OpenF1 has paused public access because an F1 session is on air..."
  }
}
```

HTTP **503**. Other OpenF1 failures: **502**, `code: "OPENF1_UPSTREAM"`.

### 4.4 Chat

| Method | Path | Body | Response |
| --- | --- | --- | --- |
| `POST` | `/api/chat` | `{ message, thread_id?, year?, meeting_key? }` | `{ thread_id, answer, layers, trace }` |
| `POST` | `/api/chat/stream` | same | SSE `handoff` / `result` |
| `GET` | `/api/chat/{thread_id}` | — | Snapshot |

---

## 5. LangGraph (Phase 4)

### 5.1 `F1DashboardState`

```python
class F1DashboardState(TypedDict):
    messages: list
    user_query: str
    thread_id: str
    season_year: int | None
    meeting_key: int | None
    circuit_name: str | None
    intent: str   # championship_projection | constructor_finance | driver_roi | ...
    route: str    # data_analyst | generalist_direct
    routing_rationale: str
    analysis_plan: list
    selected_tools: list
    tool_calls: list
    raw_payloads: list
    synthesis: str
    needs_more_data: bool
    answer: str
    trace: dict
```

No `timeline` intent. Commercial questions route to **data_analyst** (`get_finance_estimates` store). “Look up / search online” routes to **researcher** (`search_commercial` then store). Researcher never invents USD amounts.

### 5.2 Topology

```
START → generalist
          ├─ generalist_direct → technical_manager → END
          ├─ researcher ⇄ tools → technical_manager → END
          └─ data_analyst ⇄ tools → strategic_analyst → technical_manager → END
```

- **Generalist:** no OpenF1; binds `season_year` / `meeting_key`. “This year” → calendar year **2026**.
- **Data Analyst:** OpenF1 + fact store; loops while `needs_more_data`.
- **Strategic Analyst:** championship projection from retrieved payloads (pace, DNFs, remaining calendar, teammate cushion).
- **Researcher:** web search (Tavily), cite, write store; then read store. No invented dollars.
- **Technical Manager:** never fetches; emits `routing`, `reasoning_path`, `execution_trace`, `api_calls`, `pipelines`, `agent_handoffs`.

Scoring and the eight interview tests: [EVALUATION.md](./EVALUATION.md).

---

## 6. End-to-end flow

1. User picks season and optionally a circuit. URL + `loadDashboard` share `meeting_key`.
2. Manufacturer tab: constructor points + labeled financials + CPP chart.
3. Driver tab: five FIFA cards + five-line progression.
4. Summary: leader KPIs + insights (no timeline).
5. Co-Pilot under the ledger; title questions hit live sport APIs; UI shows **server** `layers` + `trace`.

---

## 7. Quality

| Concern | Approach |
| --- | --- |
| OpenF1 3 req/s | Throttle, cache, single `/api/dashboard` |
| 404 | Empty list, not 502 |
| Live GP lock | `F1_LIVE_LOCK` |
| IPv6 `localhost` | Bind/fetch `127.0.0.1` |
| Stale circuit | Payload keyed by `meeting_key`; remount widgets |
| Finance vs sport | Tests: constructor points ≠ driver table; CPP = cap/points; FER = salary/points; dashboard does not call Tavily; frozen year not overwritten without `force` |
| Search accuracy | Domain allowlist; sanity bounds; conflict if >20% spread; no LLM-invented USD |
| Compliance | Estimates labeled; no gambling execution; no live timing |

See [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for Git-tracked phases.
