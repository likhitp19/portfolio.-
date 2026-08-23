from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

LOGGER = logging.getLogger(__name__)
TABLE = "commercial_facts"


class SupabaseFactsError(RuntimeError):
    pass


class SupabaseTableMissing(SupabaseFactsError):
    pass


def supabase_configured() -> bool:
    return bool(settings.supabase_url.strip() and settings.supabase_anon_key.strip())


class SupabaseFacts:
    def __init__(self) -> None:
        self.base = settings.supabase_url.rstrip("/")
        key = settings.supabase_anon_key.strip()
        self._headers = {
            "apikey": key,
            "Authorization": "Bearer {0}".format(key),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._http = httpx.Client(timeout=20.0, headers=self._headers)

    def close(self) -> None:
        self._http.close()

    def _url(self) -> str:
        return "{0}/rest/v1/{1}".format(self.base, TABLE)

    def ping(self) -> None:
        response = self._http.get(
            self._url(),
            params={"select": "entity_key", "limit": "1"},
        )
        if response.status_code == 404 or "PGRST205" in response.text:
            raise SupabaseTableMissing(
                "Supabase table public.commercial_facts is missing. "
                "Run backend/app/data/commercial_facts.sql in the SQL Editor."
            )
        if response.status_code >= 400:
            raise SupabaseFactsError(
                "Supabase facts read failed ({0}).".format(response.status_code)
            )

    def get_exact(
        self,
        entity_type: str,
        entity_key: str,
        season_year: int,
        metric: str,
    ) -> Optional[Dict[str, Any]]:
        response = self._http.get(
            self._url(),
            params={
                "entity_type": "eq.{0}".format(entity_type),
                "entity_key": "eq.{0}".format(entity_key),
                "season_year": "eq.{0}".format(season_year),
                "metric": "eq.{0}".format(metric),
                "select": "*",
                "limit": "1",
            },
        )
        self._raise_for(response)
        rows = response.json()
        if not rows:
            return None
        return _normalize(rows[0])

    def list_year(self, season_year: int) -> List[Dict[str, Any]]:
        response = self._http.get(
            self._url(),
            params={
                "season_year": "eq.{0}".format(season_year),
                "select": "*",
                "order": "entity_type,entity_key,metric",
            },
        )
        self._raise_for(response)
        return [_normalize(row) for row in response.json()]

    def list_all(self) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        start = 0
        page = 1000
        while True:
            response = self._http.get(
                self._url(),
                params={"select": "*", "order": "entity_type,entity_key,season_year,metric"},
                headers={**self._headers, "Range": "{0}-{1}".format(start, start + page - 1)},
            )
            self._raise_for(response)
            chunk = response.json()
            rows.extend(_normalize(row) for row in chunk)
            if len(chunk) < page:
                break
            start += page
        return rows

    def nearest_year(self, season_year: int) -> Optional[int]:
        response = self._http.get(
            self._url(),
            params={"select": "season_year"},
        )
        self._raise_for(response)
        years = {int(row["season_year"]) for row in response.json() if row.get("season_year") is not None}
        if not years:
            return None
        return min(years, key=lambda year: abs(year - season_year))

    def upsert(self, fact: Dict[str, Any]) -> None:
        payload = {
            "entity_type": fact["entity_type"],
            "entity_key": fact["entity_key"],
            "season_year": int(fact["season_year"]),
            "metric": fact["metric"],
            "value_usd": fact.get("value_usd"),
            "status": fact.get("status") or "estimate",
            "confidence": fact.get("confidence"),
            "source_url": fact.get("source_url"),
            "source_title": fact.get("source_title"),
            "snippet": fact.get("snippet"),
            "retrieved_at": fact.get("retrieved_at"),
            "frozen": bool(fact.get("frozen")),
            "value_low": fact.get("value_low"),
            "value_high": fact.get("value_high"),
        }
        response = self._http.post(
            self._url(),
            params={"on_conflict": "entity_type,entity_key,season_year,metric"},
            headers={
                **self._headers,
                "Prefer": "resolution=merge-duplicates,return=minimal",
            },
            json=payload,
        )
        self._raise_for(response)

    def _raise_for(self, response: httpx.Response) -> None:
        if response.status_code == 404 or "PGRST205" in response.text:
            raise SupabaseTableMissing(
                "Supabase table public.commercial_facts is missing. "
                "Run backend/app/data/commercial_facts.sql in the SQL Editor."
            )
        if response.status_code >= 400:
            LOGGER.warning("Supabase facts HTTP %s", response.status_code)
            raise SupabaseFactsError("Supabase facts request failed ({0}).".format(response.status_code))


def _normalize(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    frozen = out.get("frozen")
    if isinstance(frozen, bool):
        out["frozen"] = 1 if frozen else 0
    return out
