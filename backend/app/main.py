from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.integrations.openf1 import OpenF1Client
from app.routers.chat import router as chat_router
from app.routers.dashboard import router as dashboard_router
from app.runtime import get_client, set_client, set_fact_store
from app.services.dashboard import dashboard_overview
from app.services.fact_store import FactStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    owned = False
    try:
        client = get_client()
    except RuntimeError:
        client = OpenF1Client(settings.openf1_base_url)
        set_client(client)
        owned = True
    set_fact_store(FactStore())
    if settings.dashboard_preload:
        import asyncio

        async def _preload() -> None:
            await asyncio.sleep(0.5)
            try:
                live = get_client()
            except RuntimeError:
                return
            for year in (2024, 2025, 2026):
                try:
                    await dashboard_overview(live, year, None)
                except Exception:
                    continue

        asyncio.create_task(_preload())
    yield
    if owned:
        await client.aclose()


app = FastAPI(title="F1 Dashboard API", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(chat_router)


@app.get("/health")
def health() -> dict:
    from app.runtime import get_fact_store

    store = get_fact_store()
    return {"status": "ok", "facts_backend": getattr(store, "backend", getattr(store, "backend_name", "sqlite")), "facts_count": store.count()}
