# Deploy — Paddock Ledger

Two services: **Vercel (Next.js)** and **Railway (FastAPI)**. Chat and a cold dashboard can take tens of seconds. Do not put FastAPI on Vercel serverless. Never commit `.env`.

```
Browser ── /season/* ──► Vercel (static + client JS)
Browser ── /api/*    ──► Railway (FastAPI)   ← NEXT_PUBLIC_API_URL
```

The UI does **not** load OpenF1 on the Vercel server. Nav, dashboard, and chat all call Railway from the browser so Hobby’s ~10s serverless limit cannot kill a 45s season fetch.

---

## 1. Railway (API)

1. New project → **Deploy from GitHub** → `likhitp19/portfolio.-` (or this repo).
2. Leave **Root Directory empty**. The repo-root `Dockerfile` copies `backend/`.
   - If you instead set Root Directory to `backend/`, Railway uses `backend/Dockerfile`.
3. Public HTTPS domain (Generate Domain). Health: `GET https://<api>.up.railway.app/health`.
4. Variables (same names as `backend/.env.example`):

| Name | Notes |
| --- | --- |
| `CORS_ORIGINS` | `https://<your-app>.vercel.app` plus `http://localhost:3000` if you test locally against prod API |
| `CORS_ORIGIN_REGEX` | Default `https://.*\.vercel\.app` covers previews. Keep it. |
| `DEEPSEEK_API_KEY` | Chat routing; heuristics still work if empty |
| `OPENROUTER_API_KEY` | Race Steward (Qwen-VL + DeepSeek-R1 via OpenRouter). Optional; without it steward uses hint + OpenF1 + heuristic verdict |
| `STEWARD_VISION_MODEL` / `STEWARD_REASON_MODEL` | Defaults in `backend/.env.example` |
| `TAVILY_API_KEY` | Only for “look up online” |
| `SUPABASE_URL` / `SUPABASE_ANON_KEY` | Durable commercial facts. Create `commercial_facts` with `backend/app/data/commercial_facts.sql` first. |
| `LLM_BASE_URL` / `LLM_MODEL` | Defaults in `backend/.env.example` |
| `PORT` | Railway sets this. Do not override. |

If Supabase is configured and the table exists, facts persist across deploys. Otherwise SQLite at `/tmp/commercial_facts.sqlite` is seeded on boot (ephemeral).

---

## 2. Vercel (UI)

1. Import the **same GitHub repo**.
2. **Root Directory: `frontend`**. Framework: Next.js. Node 20.
3. Variables:

| Name | Value |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | `https://<railway-api>.up.railway.app` (**no trailing slash**) |
| `API_INTERNAL_URL` | Same URL (rewrites if anything still hits same-origin `/api`) |

4. Redeploy after changing `NEXT_PUBLIC_*` (it is baked into the client bundle).
5. Copy the production URL (`https://….vercel.app`) into Railway `CORS_ORIGINS` if you want an exact origin in addition to the regex.

---

## 3. CORS

Browser `POST /api/chat` and `GET /api/dashboard` go to Railway. Railway must allow the Vercel origin. The default regex matches `*.vercel.app`. A custom domain on Vercel must be added to `CORS_ORIGINS`.

---

## 4. Alternative: Railway only

Two Railway services from one repo:

- **api** — empty root (repo `Dockerfile`) or `backend/`
- **web** — Root Directory `frontend`, `npm run build && npm run start`, `NEXT_PUBLIC_API_URL` = public API URL

---

## 5. Smoke after deploy

1. Open `/` → **2026** season ledger (KPIs, CPP chart, constructor book) then co-pilot (~15–45s for dashboard).
2. Starter **Who is projected to win the Championship this year…** → layered report + trace (may take a minute on first OpenF1 calendar call).
3. Finance still works if you type e.g. “best cost-per-point in 2024”.
4. `GET /health` on Railway → `status: ok`. After Supabase is wired, `facts_backend` is `supabase` and `facts_count` is ~40+.
5. Manufacturer **Race wins** should track the season (not a handful of GPs from one Ergast page).

Supabase one-time SQL and seed behavior: [FACTS.md](./FACTS.md).
