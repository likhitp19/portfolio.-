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
| `TAVILY_API_KEY` | Only for “look up online” |
| `LLM_BASE_URL` / `LLM_MODEL` | Defaults in `backend/.env.example` |
| `PORT` | Railway sets this. Do not override. |

SQLite lives at `/tmp/commercial_facts.sqlite` in the image (seed on boot). It is **not** durable across deploys; that is fine for the interview.

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

1. Open the Vercel URL → season dashboard fills in (may take ~15–45s).
2. Chip **Ferrari vs McLaren CPP (2023)** → finance answer + source tag.
3. Chip **1998 Telemetry Boundary Test** → empty `api_calls`.
4. `GET /health` on Railway → `{"status":"ok"}`.
