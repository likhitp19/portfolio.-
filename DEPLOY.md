# Deploy — Paddock Ledger

Two services: **Next.js UI** and **FastAPI + LangGraph**. Chat can take up to ~45s. Dollars stay in the fact store; never commit `.env`.

## Recommendation

**Use the best host per component. Do not standardize on Railway out of habit.**

| Piece | Host | Why |
| --- | --- | --- |
| Frontend | **Vercel** | Native Next.js App Router, previews, CDN |
| Backend | **Railway** | Long-lived Python, 45s chat, SQLite seed, no Vercel serverless limit for FastAPI |

**Railway for both** is a good *ops* choice (one bill, one private network, fewer CORS surprises). It is not a better *Next.js* host than Vercel.

**Do not** put FastAPI on Vercel serverless. LangGraph + OpenF1/Jolpica + 45s chat does not fit that runtime.

This repo is wired for **Vercel UI + Railway API**. Browser chat should call Railway **directly** (`NEXT_PUBLIC_API_URL`) so Vercel’s rewrite timeout cannot kill the desk.

```
Browser ── /season/* ──► Vercel (Next.js)
Browser ── /api/chat ──► Railway (FastAPI)   ← NEXT_PUBLIC_API_URL
Next SSR ── /api/*  ──► Railway              ← API_INTERNAL_URL rewrite
```

---

## 1. GitHub

Public repo from `interview/` (not the parent `projects/` tree). `.env` is gitignored.

---

## 2. Railway (API)

1. New project → deploy from GitHub → **root directory `backend/`**.
2. Use the Dockerfile in `backend/`.
3. Variables:

| Name | Notes |
| --- | --- |
| `CORS_ORIGINS` | `https://<vercel-app>.vercel.app` (comma-separate preview URLs if needed) |
| `DEEPSEEK_API_KEY` | Chat routing; heuristics still work if empty |
| `TAVILY_API_KEY` | Only for “look up online” |
| `LLM_BASE_URL` / `LLM_MODEL` | Defaults in `backend/.env.example` |
| `COMMERCIAL_FACTS_DB` | Optional. Ephemeral disk is fine for a demo (seed reloads). |

4. Generate a public HTTPS domain. Health: `GET https://<api>/health`.
5. SQLite on Railway is **not durable** across deploys unless you add a volume. Demo seed is enough for the interview.

---

## 3. Vercel (UI)

1. Import the same GitHub repo → **root directory `frontend/`**.
2. Framework: Next.js.
3. Variables:

| Name | Value |
| --- | --- |
| `API_INTERNAL_URL` | `https://<railway-api>.up.railway.app` (no trailing slash) |
| `NEXT_PUBLIC_API_URL` | Same Railway origin (browser chat + CORS) |

4. `next.config.ts` rewrites `/api/:path*` to `API_INTERNAL_URL` for server-side fetches. Chat uses `NEXT_PUBLIC_API_URL` in the browser.

---

## 4. CORS

Railway `CORS_ORIGINS` must include the Vercel origin or the browser will block `POST /api/chat`.

---

## 5. Alternative: Railway only

Two Railway services from one repo:

- **api** — `backend/`, Dockerfile, `$PORT`
- **web** — `frontend/`, `npm run build && npm run start`, `API_INTERNAL_URL=http://api.railway.internal:PORT`

Use this if you want one vendor and longer Next server timeouts. Still keep secrets on Railway, not in git.

---

## 6. Smoke after deploy

1. Open the Vercel URL → season dashboard loads.
2. Chip **Ferrari vs McLaren CPP (2023)** → finance answer + source tag, not standings snapshots.
3. Chip **1998 Telemetry Boundary Test** → no OpenF1 retries, empty `api_calls`.
4. `GET /health` on Railway → `{"status":"ok"}`.
