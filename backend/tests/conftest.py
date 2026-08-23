import pytest

from app.config import settings
from app.integrations.search import SearchClient
from app.runtime import set_client, set_fact_store, set_search_client
from app.services.dashboard import clear_dashboard_cache
from app.services.fact_store import FactStore
from tests.fakes import FakeOpenF1Client


@pytest.fixture(autouse=True)
def disable_live_llm(monkeypatch):
    """Graph tests must stay deterministic; never hit DeepSeek from backend/.env."""
    monkeypatch.setattr(settings, "deepseek_api_key", "")
    monkeypatch.setattr(settings, "openai_api_key", "")
    monkeypatch.setattr(settings, "dashboard_preload", False)
    monkeypatch.setattr(settings, "supabase_url", "")
    monkeypatch.setattr(settings, "supabase_anon_key", "")


@pytest.fixture(autouse=True)
def fake_openf1():
    client = FakeOpenF1Client()
    set_client(client)
    yield client


@pytest.fixture(autouse=True)
def fact_backend():
    clear_dashboard_cache()
    store = FactStore(":memory:")
    search = SearchClient()
    set_fact_store(store)
    set_search_client(search)
    yield store, search
