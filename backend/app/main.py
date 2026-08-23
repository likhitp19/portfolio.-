from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.integrations.openf1 import OpenF1Client
from app.routers.chat import router as chat_router
from app.routers.dashboard import router as dashboard_router
from app.runtime import get_client, set_client, set_fact_store
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
    yield
    if owned:
        await client.aclose()


app = FastAPI(title="F1 Dashboard API", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(chat_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
