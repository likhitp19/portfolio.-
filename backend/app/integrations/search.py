from __future__ import annotations

import re
from typing import Any, Dict, List
from urllib.parse import urlparse

import httpx

from app.config import settings

PREFERRED_HOSTS = (
    "fia.com",
    "formula1.com",
    "reuters.com",
    "bbc.com",
    "bbc.co.uk",
    "autosport.com",
    "the-race.com",
    "racefans.net",
    "forbes.com",
    "sportico.com",
)

_AMOUNT = re.compile(
    r"(?:usd|us\$|\$)\s*([0-9]+(?:\.[0-9]+)?)\s*(billion|million|bn|b|m)?",
    re.I,
)


def host_allowed(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower().lstrip("www.")
    return any(host == allowed or host.endswith("." + allowed) for allowed in PREFERRED_HOSTS)


def parse_usd(text: str) -> List[float]:
    found: List[float] = []
    for match in _AMOUNT.finditer(text or ""):
        number = float(match.group(1))
        unit = (match.group(2) or "").lower()
        if unit in {"billion", "bn", "b"}:
            number *= 1_000_000_000
        elif unit in {"million", "m"}:
            number *= 1_000_000
        found.append(number)
    return found


class SearchUnavailable(Exception):
    """403, proxy, or timeout talking to Tavily."""


class SearchClient:
    """Tavily search. Dashboard reads must never call this."""

    def __init__(self) -> None:
        self.calls: List[str] = []

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        self.calls.append(query)
        key = (settings.tavily_api_key or "").strip()
        if not key:
            return []
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={"api_key": key, "query": query, "max_results": max_results, "search_depth": "basic"},
                )
        except (httpx.TimeoutException, httpx.NetworkError, httpx.ProxyError) as exc:
            raise SearchUnavailable(str(exc)) from exc
        if response.status_code in {401, 403} or response.status_code >= 500:
            raise SearchUnavailable("HTTP {0}".format(response.status_code))
        if response.status_code >= 400:
            return []
        payload = response.json()
        hits = []
        for item in payload.get("results") or []:
            url = str(item.get("url") or "")
            if url and not host_allowed(url):
                continue
            hits.append(
                {
                    "url": url,
                    "title": item.get("title"),
                    "content": item.get("content") or item.get("snippet") or "",
                }
            )
        return hits
