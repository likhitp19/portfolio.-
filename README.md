# F1 Business Intelligence Dashboard & Multi-Agent Analyst

A premium, dark-themed **Formula 1 management console** for two audiences that sit on the same data contract (`year`, `meeting_key`, `session_key`):

1. **Business analysts & commercial teams** — constructor economics (valuations, budget cap, cost-per-point, wins per manufacturer), driver **ROI**, sponsor- and betting-oriented insights.
2. **Technical engineers** — reactive circuit drill-down, honest OpenF1 championship math, and a **LangGraph** analyst that shows *how* a number was derived (APIs, pipelines, routing).

This is **not** a live timing app and **not** a chronological race-control timeline. The product story is: *if you ran a team or a book, what is a point, a driver, and a constructor actually worth?*

| Document | Purpose |
| --- | --- |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Domain, DTOs, Shadcn/Recharts choices, FastAPI, `F1DashboardState`, error `F1_LIVE_LOCK` |
| [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) | Five Git-tracked phases (setup → manufacturer finance → driver gamification → LangGraph → chat + trace) |
| [EVALUATION.md](./EVALUATION.md) | Eight-test agent rubric: routing, orchestration, transformation, answer quality, API cleanliness |
| [DEPLOY.md](./DEPLOY.md) | Vercel UI + Railway API, env vars, CORS, smoke checks |
| [STITCH.md](./STITCH.md) | Google Stitch MCP for design screens (editor only) |

**GitHub (this app only):** [`likhitp19/portfolio.-`](https://github.com/likhitp19/portfolio.-) — clone/push **`interview/`**, not the parent `projects/` folder.

**Production:** Vercel (UI) + Railway (API). The browser calls Railway directly (`NEXT_PUBLIC_API_URL`). See [DEPLOY.md](./DEPLOY.md). Paste secrets in the host dashboards — no keys in git.

**Editor MCP:** [STITCH.md](./STITCH.md) — Google Stitch via [`npx @_davideast/stitch-mcp proxy`](https://stitch.withgoogle.com/docs/mcp/setup). Supabase MCP is already in `.mcp.json`.

---

## Purpose

### Dual audience

| Audience | What they must see in a demo |
| --- | --- |
| **Business analyst** | Team enterprise value vs FIA budget cap; **cost-per-point**; driver salary vs championship points; “who is overpaid relative to output?” |
| **Technical engineer** | Constructor points from `championship_teams` (never a relabeled driver table); completed-race-only OpenF1; LangGraph **trace** with real `api_calls` |

### Surfaces

- **All Circuits** season view vs **one GP** (`meeting_key`). Changing the circuit **must** navigate and **re-fetch** `/api/dashboard` so no widget keeps the previous meeting.
- **Manufacturer (business view):** constructor points + **cited commercial facts** (valuations, FIA budget cap, cost-per-point, wins per manufacturer). OpenF1 has **no** team value or salary fields — those come from a **search API + persistent fact store**, not invented mocks on each request.
- **Driver (gamified ROI):** top **5** championship cards with official F1 DAM **headshots**, stored salary estimates, points, **FER** = salary / points. Teammate matrix cards show **constructor logos**.
- **Overall Summary:** leader, gap to P2, races completed; **business insights grid** (fastest lap, total DNFs, top-3 finishes). **No event timeline.**
- **Interview page flow:** **analytics first** (KPIs, cost-per-point, constructor book, era/yield charts), **Executive Co-Pilot below**. Default season is **2026** (`/` and `/season/2025` redirect there).
- **Agent chat:** Generalist → Data Analyst ⇄ OpenF1 tools → Strategic Analyst (title projection) → Technical Manager. `POST /api/chat/stream` emits agent handoffs. Client **never invents** `trace`. Championship starter: *Who is projected to win the Championship this year, and what does the data say?*

### Data policy

- **≥10 seasons** in the year dropdown (rolling window, e.g. 2017–2026).
- **Sporting:** OpenF1 for 2023+ completed races; **Jolpica/Ergast** when OpenF1 has no meeting list (older years). Never live timing. **`F1_LIVE_LOCK`** if OpenF1 is locked during a session.
- **Commercial:** search once → **fact store** (Supabase when configured, else SQLite). Frozen for completed years. See [FACTS.md](./FACTS.md).

### Ship

Next.js **is** the React site. **Production:** Vercel (UI) + Railway (API). See [DEPLOY.md](./DEPLOY.md). Paste secrets in the host dashboards — no keys in git.

---

## Tech stack

| Layer | Choice | Why |
| --- | --- | --- |
| Frontend | **Next.js** App Router | Season/circuit in the URL; dashboard loads from the browser against FastAPI |
| UI | **Tailwind** + **Shadcn** (`Card`, `Badge`, `Tabs`, `HoverCard`, `Table`, `Alert`) | Premium dark console; driver ROI cards with DAM portraits; hover for valuation footnotes |
| Charts | **Recharts** | Cost-per-point bars; top-5 points progression; custom tooltips (USD + pts) |
| Backend | **FastAPI** | Dashboard aggregate (no LLM) + `POST /api/chat` |
| Sporting data | **OpenF1 v1** | Meetings, sessions, championship, results, laps — completed sessions only |
| Commercial facts | **Search API** (Tavily, pluggable) + **SQLite and optional Supabase** | Valuations, cap headlines, salaries — cited, cached, historical years frozen |
| Agents | **LangGraph** | Generalist → Data Analyst ⇄ tools → Strategic Analyst (title fight) → Technical Manager |

```
.
├── README.md
├── ARCHITECTURE.md
├── IMPLEMENTATION_PLAN.md
├── frontend/          # Next.js + Shadcn + Recharts
└── backend/           # FastAPI + LangGraph + OpenF1 + search + fact store
```

Browser calls **same-origin `/api/*`**. Next.js rewrites to FastAPI at `http://127.0.0.1:8000` (use `127.0.0.1`, not `localhost`, to avoid IPv6 miss).

---

## Local development

Prerequisites: **Node.js 20+**, **Python 3.11+** (3.9 works with the current venv).

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- Docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

Prefer **no `--reload`** while demoing.

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # API_INTERNAL_URL=http://127.0.0.1:8000
npm run dev
```

- App: `http://127.0.0.1:3000` → **`/season/2026`**. Season dropdown still covers the rolling window.

Backend tests: `cd backend && source .venv/bin/activate && pytest -q`.

### Publish this repo

```bash
cd /path/to/interview          # nested git repo — not ~/Documents/projects
git push origin main           # git@github.com:likhitp19/portfolio.-.git
```

Vercel (root `frontend`) and Railway (repo-root Docker) redeploy from `main`. Do not Publish the parent `projects/` folder.

**Demo chat:** one starter (“Who is projected to win the Championship this year…”) plus follow-ups after the report. “This year” is **2026**. Title answers come from live OpenF1/Jolpica standings, race classifications, and F1 DAM portraits — not a cached paragraph. If Tavily 403s/timeouts, the researcher uses the fact store + `MOCK_FINANCIAL_DATA`; the Technical Manager tape records the sandbox notice. Constructor **wins** come from paginated Jolpica / WCC `wins`.

---

## Environment

| Variable | Where | Purpose |
| --- | --- | --- |
| `OPENF1_BASE_URL` | backend | Default `https://api.openf1.org/v1`. ~3 req/s unauthenticated. |
| `OPENF1_USERNAME` / `OPENF1_PASSWORD` | backend | Optional. Not required for historical use. |
| `OPENF1_ACCESS_TOKEN` | backend | Optional Bearer. |
| `TAVILY_API_KEY` | backend | Commercial search (Phase 2). Not used on dashboard GET. |
| `SUPABASE_URL` / `SUPABASE_ANON_KEY` | backend | Durable facts. Run `backend/app/data/commercial_facts.sql` once, then restart API. |
| `DASHBOARD_PRELOAD` | backend | Default true. Warms 2024/2025/2026 dashboard cache on boot. |
| `JOLPICA_BASE_URL` | backend | Default `https://api.jolpi.ca/ergast/f1` for pre-OpenF1 seasons. |
| `DEEPSEEK_API_KEY` | backend | Optional. [DeepSeek API](https://api-docs.deepseek.com/). Heuristics work if empty. |
| `LLM_BASE_URL` | backend | Default `https://api.deepseek.com` |
| `LLM_MODEL` | backend | Default `deepseek-v4-flash` (or `deepseek-v4-pro`) |
| `OPENAI_API_KEY` | backend | Fallback if `DEEPSEEK_API_KEY` is unset (same OpenAI SDK shape) |
| `CORS_ORIGINS` | backend | Explicit origins, e.g. Vercel production URL |
| `CORS_ORIGIN_REGEX` | backend | Default `https://.*\.vercel\.app` |
| `API_INTERNAL_URL` | frontend | FastAPI origin for leftover same-origin rewrites |
| `NEXT_PUBLIC_API_URL` | frontend (browser) | **Required on Vercel.** Railway HTTPS origin, no trailing slash |

---

## Product principles

1. **Constructor honesty** — Manufacturer tab points come from constructor championship data, never driver points dressed as teams.
2. **Cited commercial facts, not silent mocks** — Valuation, salary, and cap headlines come from the **fact store** (filled by search + review). UI `Badge` shows Estimate / Official / Conflict. HoverCard lists **source URL and retrieved date**. Betting copy is insight, not a market.
3. **Search once, store forever (for history)** — Completed years are **immutable** after a confirmed write. The current championship year may refresh on a long TTL (days/weeks), never per HTTP request.
4. **One circuit, one payload** — `meeting_key` in the path and in `/api/dashboard`. Stale GP data is a bug.
5. **Historical sport 2023+ only** — completed races; `F1_LIVE_LOCK` when OpenF1 is globally locked.
6. **Trace is server-owned** — chat UI renders Technical Manager output only; search calls appear as `search_commercial` in `api_calls` when they actually ran.

See [ARCHITECTURE.md](./ARCHITECTURE.md) for formulas, Shadcn composition, and routes.
