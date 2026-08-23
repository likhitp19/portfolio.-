from typing import Optional

from app.integrations.openf1 import OpenF1Client
from app.integrations.search import SearchClient
from app.services.fact_store import FactStore

_client: Optional[OpenF1Client] = None
_store: Optional[FactStore] = None
_search: Optional[SearchClient] = None


def set_client(client: OpenF1Client) -> None:
    global _client
    _client = client


def get_client() -> OpenF1Client:
    if _client is None:
        raise RuntimeError("OpenF1 client is not initialized")
    return _client


def set_fact_store(store: FactStore) -> None:
    global _store
    _store = store


def get_fact_store() -> FactStore:
    global _store
    if _store is None:
        _store = FactStore(":memory:")
    return _store


def set_search_client(search: SearchClient) -> None:
    global _search
    _search = search


def get_search_client() -> SearchClient:
    global _search
    if _search is None:
        _search = SearchClient()
    return _search
