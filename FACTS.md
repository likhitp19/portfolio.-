# Commercial facts, cache, and Supabase

OpenF1/Jolpica have **points, results, and sessions**. They do **not** have team valuations, driver retainers, or the FIA cost cap. Those live in a **cited fact store**. Dashboard GET and chat `get_finance_estimates` **only read the store**. They never search the web on page load.

Full schema and accuracy rules: [ARCHITECTURE.md](./ARCHITECTURE.md) §2.2.

---

## Backends

| Backend | When | Durable? |
| --- | --- | --- |
| **SQLite** | Default, tests (`:memory:`), or Supabase table missing | File on disk. Railway container disk is **ephemeral**. |
| **Supabase** | `SUPABASE_URL` + `SUPABASE_ANON_KEY` set **and** table `public.commercial_facts` exists | Yes. Survives Railway deploys. |

On API boot (not in tests):

1. Open local SQLite and load `backend/app/data/commercial_facts.seed.json` if empty.
2. Fill any missing constructor valuations for 2023–2025 (full grid, including midfield).
3. If Supabase is reachable, **hydrate** SQLite from remote, then **push** missing seed/grid rows up.

`GET /health` includes `facts_backend` (`sqlite` or `supabase`) and `facts_count`.

---

## Create the Supabase table (once)

1. Open the Supabase project → **SQL Editor**.
2. Run [backend/app/data/commercial_facts.sql](./backend/app/data/commercial_facts.sql).
3. Restart the API (local uvicorn or Railway).

The SQL creates `public.commercial_facts`, enables RLS, and allows `anon` read/insert/update so the FastAPI process can seed with the publishable/anon key. Tighten those policies before a public production launch.

Do **not** commit `.env`. Paste `SUPABASE_URL` and `SUPABASE_ANON_KEY` only in `backend/.env` and Railway variables.

---

## What gets stored

| `entity_type` | `entity_key` | `metric` | Example |
| --- | --- | --- | --- |
| `regulation` | `fia_cost_cap` | `budget_cap_usd` | USD 135M estimate |
| `constructor` | canonical team (`mclaren`, `alpine`, …) | `valuation_usd` | Midpoint franchise estimate |
| `driver` | driver number as string | `salary_usd` | Reported retainer estimate |

Status is `estimate` unless a filing/sale is cited. Midfield teams (Aston Martin through Sauber) use the same labeled estimates as the top four so Manufacturer tab cells are not blank/`defaulted`.

Lookups fall back to the **nearest stored year** if the requested season has no row (e.g. 2025 can use 2024).

---

## Dashboard speed (timeouts)

A cold full-season dashboard used to hammer OpenF1 for constructor charts and sometimes abort in the browser.

| Layer | Behavior |
| --- | --- |
| Constructor progression | Long seasons use **Jolpica season results** (one call), not per-race OpenF1 team snapshots |
| API memory cache | `/api/dashboard` cached ~15 minutes per `(year, meeting_key)` |
| Preload | `DASHBOARD_PRELOAD=true` warms 2024 and 2025 after boot |
| Browser | `AbortSignal` **90s** so a cold Railway start can finish |

Constructor **race wins** on the Manufacturer tab are season totals from Jolpica constructor standings (`wins`) and paginated race results. A single `/results.json` page is only ~30 classification rows (about one GP); we page until `total`. Sprint sessions are not counted. **Wins / GP** uses completed grands prix, not every OpenF1 session labeled Race.

---

## Eval / chat

Finance questions (driver ROI, McLaren vs Ferrari cap efficiency, midfield investor) answer with **metric, inputs, formula**, then numbers from standings + the fact store, tagged as public financial benchmarks.

Telemetry-style H2H / stint / grid-gain questions still **do not invent** lap deltas.

---

## Local check

```bash
cd backend
source .venv/bin/activate
# SUPABASE_* already in .env
python -c "from app.services.fact_store import FactStore; s=FactStore(); print(s.backend, s.count())"
```

Expect `supabase` and a count around 40+ after the first successful attach. Then `GET http://127.0.0.1:8000/health` (`facts_backend`, `facts_count`).

---

## Driver photos and team logos

Driver cards load F1 Cloudinary DAM portraits from `frontend/lib/media.ts` (`2026Drivers` → `2025Drivers` → `2024Drivers` by last name). If the DAM 404s, `MediaAvatar` tries the next URL then initials. Constructor logos try `{slug}-logo.png` 2026–2023, then 2018 `.jpg`. Teammate list cards use the same logo chain.

---

## Railway (after this repo is on `main`)

Set the same `SUPABASE_URL` and `SUPABASE_ANON_KEY` as local `.env` in the Railway service variables, then redeploy. This environment cannot log into your Railway account.
