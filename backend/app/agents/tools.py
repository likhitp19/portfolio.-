from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.data.mock_financial import mock_facts_for_year
from app.integrations.openf1 import OpenF1HTTPError
from app.integrations.search import SearchUnavailable
from app.runtime import get_client, get_fact_store, get_search_client
from app.services.commercial import refresh_commercial_facts

SANDBOX_NOTICE = (
    "[Notice: Sandbox restricted external search; resolved via internal benchmark store]"
)

TOOL_CATALOG = {
    "list_meetings": {"method": "GET", "path": "/v1/meetings"},
    "list_sessions": {"method": "GET", "path": "/v1/sessions"},
    "get_drivers": {"method": "GET", "path": "/v1/drivers"},
    "get_championship_drivers": {"method": "GET", "path": "/v1/championship_drivers"},
    "get_championship_teams": {"method": "GET", "path": "/v1/championship_teams"},
    "get_session_result": {"method": "GET", "path": "/v1/session_result"},
    "get_laps": {"method": "GET", "path": "/v1/laps"},
    "get_position": {"method": "GET", "path": "/v1/position"},
    "get_race_control": {"method": "GET", "path": "/v1/race_control"},
    "get_weather": {"method": "GET", "path": "/v1/weather"},
    "get_finance_estimates": {"method": "GET", "path": "fact_store://commercial"},
    "search_commercial": {"method": "POST", "path": "search://tavily"},
}

PREVIEW_LIMIT = 40
FINANCE_PREVIEW_LIMIT = 120


def _merge_mock_finance(year: int, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    existing = {
        (str(row.get("entity_type")), str(row.get("entity_key")), str(row.get("metric")))
        for row in data
    }
    extra = []
    for row in mock_facts_for_year(year):
        key = (str(row["entity_type"]), str(row["entity_key"]), str(row["metric"]))
        if key not in existing:
            extra.append(row)
    return list(data) + extra


def _compact_rows(name: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if name == "list_sessions":
        races = [
            {
                "session_key": row.get("session_key"),
                "meeting_key": row.get("meeting_key"),
                "session_name": row.get("session_name") or row.get("session_type"),
                "session_type": row.get("session_type"),
                "date_start": row.get("date_start"),
            }
            for row in rows
            if str(row.get("session_name") or "") == "Race" or str(row.get("session_type") or "") == "Race"
        ]
        races.sort(key=lambda item: str(item.get("date_start") or ""))
        return races
    if name in {"get_championship_drivers", "get_championship_teams", "get_drivers"}:
        keys = (
            "driver_number",
            "full_name",
            "name_acronym",
            "team_name",
            "points",
            "points_current",
            "position",
            "position_current",
            "session_key",
        )
        compact = []
        for row in rows:
            compact.append({key: row.get(key) for key in keys if key in row or row.get(key) is not None})
        return compact[:PREVIEW_LIMIT]
    if name == "get_session_result":
        compact = []
        for row in rows:
            compact.append(
                {
                    "position": row.get("position"),
                    "driver_number": row.get("driver_number"),
                    "full_name": row.get("full_name") or row.get("name_acronym"),
                    "dnf": row.get("dnf"),
                }
            )
        return compact[:PREVIEW_LIMIT]
    return rows[:PREVIEW_LIMIT]


async def execute_tool(name: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    args = dict(args or {})
    meta = TOOL_CATALOG.get(name)
    if meta is None:
        return {
            "tool": name,
            "args": args,
            "method": "GET",
            "path": "",
            "params": args,
            "status": "error",
            "error": "Unknown tool",
            "record_count": 0,
            "preview": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    if name == "get_finance_estimates":
        store = get_fact_store()
        year = args.get("year")
        used_year = int(year) if year else None
        fallback = False
        if year:
            data, used_year, fallback = store.list_year_with_fallback(int(year))
            data = _merge_mock_finance(int(used_year or year), list(data))
        else:
            data = []
        params = dict(args)
        params["fact_year"] = used_year
        params["fact_year_fallback"] = fallback
        return {
            "tool": name,
            "args": args,
            "method": meta["method"],
            "path": meta["path"],
            "params": params,
            "status": "ok",
            "error": None,
            "record_count": len(data),
            "preview": data[:FINANCE_PREVIEW_LIMIT],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fact_year": used_year,
            "fact_year_fallback": fallback,
        }
    if name == "search_commercial":
        search = get_search_client()
        query = str(args.get("query") or "")
        year = int(args.get("year") or datetime.now(timezone.utc).year)
        teams = list(args.get("team_names") or [])
        try:
            hits = await search.search(query) if query else []
            refresh = await refresh_commercial_facts(get_fact_store(), search, year, teams, force=False)
            preview = hits[:PREVIEW_LIMIT] or [refresh]
            return {
                "tool": name,
                "args": args,
                "method": meta["method"],
                "path": meta["path"],
                "params": args,
                "status": "ok",
                "error": None,
                "record_count": len(hits) or int(refresh.get("searched") or 0),
                "preview": preview,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sandbox_fallback": False,
            }
        except (SearchUnavailable, httpx.TimeoutException, httpx.ProxyError, OSError):
            store = get_fact_store()
            data, used_year, fallback = store.list_year_with_fallback(year)
            data = _merge_mock_finance(int(used_year or year), list(data))
            return {
                "tool": name,
                "args": args,
                "method": meta["method"],
                "path": meta["path"],
                "params": {**args, "fact_year": used_year, "sandbox_fallback": True},
                "status": "degraded",
                "error": SANDBOX_NOTICE,
                "record_count": len(data),
                "preview": data[:FINANCE_PREVIEW_LIMIT],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sandbox_fallback": True,
            }
    client = get_client()
    method = getattr(client, name, None)
    if method is None:
        return {
            "tool": name,
            "args": args,
            "method": meta["method"],
            "path": meta["path"],
            "params": args,
            "status": "error",
            "error": "Unknown tool",
            "record_count": 0,
            "preview": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    try:
        data = await method(**args)
        year = args.get("year")
        if name in {"get_championship_drivers", "get_championship_teams"} and not data and year:
            sessions = await client.list_sessions(year=int(year))
            races = [
                row
                for row in sessions
                if str(row.get("session_name") or "") == "Race" or str(row.get("session_type") or "") == "Race"
            ]
            races.sort(key=lambda row: str(row.get("date_start") or row.get("date_end") or ""))
            if races:
                data = await method(session_key=races[-1].get("session_key"))
        if name in {"get_championship_drivers", "get_championship_teams"} and not data and year:
            from app.integrations.jolpica import JolpicaClient

            jolpica = JolpicaClient()
            try:
                if name == "get_championship_teams":
                    data = await jolpica.constructor_standings(int(year))
                else:
                    data = await jolpica.driver_standings(int(year))
            finally:
                await jolpica.aclose()
        preview = _compact_rows(name, data)
        return {
            "tool": name,
            "args": args,
            "method": meta["method"],
            "path": meta["path"],
            "params": args,
            "status": "ok",
            "error": None,
            "record_count": len(data),
            "preview": preview,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except OpenF1HTTPError as exc:
        return {
            "tool": name,
            "args": args,
            "method": meta["method"],
            "path": meta["path"],
            "params": args,
            "status": "error",
            "error": str(exc),
            "record_count": 0,
            "preview": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
