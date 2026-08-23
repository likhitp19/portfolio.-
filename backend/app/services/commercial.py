from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.integrations.search import SearchClient, parse_usd
from app.services.fact_store import DEFAULT_CAP_USD, FactStore, in_bounds


async def refresh_commercial_facts(
    store: FactStore,
    search: SearchClient,
    year: int,
    team_names: List[str],
    force: bool = False,
) -> Dict[str, Any]:
    wrote = 0
    skipped = 0
    searched = 0
    cap = store.get("regulation", "fia_cost_cap", year, "budget_cap_usd")
    if cap is None:
        hits = await search.search("FIA Formula 1 cost cap USD {0}".format(year))
        searched += 1
        parsed = _pick_amount(hits, "budget_cap_usd")
        store.upsert(
            {
                "entity_type": "regulation",
                "entity_key": "fia_cost_cap",
                "season_year": year,
                "metric": "budget_cap_usd",
                "value_usd": parsed["value"] if parsed else DEFAULT_CAP_USD,
                "status": "estimate" if parsed else "defaulted",
                "source_url": parsed.get("url") if parsed else None,
                "source_title": parsed.get("title") if parsed else "Default FIA-style cap",
                "snippet": parsed.get("snippet") if parsed else "No cited cap; using USD 135M default.",
            },
            force=force,
        )
        wrote += 1
    else:
        skipped += 1

    for team in team_names:
        existing = store.get("constructor", team, year, "valuation_usd")
        if existing and not force:
            skipped += 1
            continue
        hits = await search.search("{0} F1 team valuation USD {1}".format(team, year))
        searched += 1
        parsed = _pick_amount(hits, "valuation_usd")
        ok = store.upsert(
            {
                "entity_type": "constructor",
                "entity_key": team,
                "season_year": year,
                "metric": "valuation_usd",
                "value_usd": parsed["value"] if parsed else None,
                "status": "estimate" if parsed else "defaulted",
                "source_url": parsed.get("url") if parsed else None,
                "source_title": parsed.get("title") if parsed else None,
                "snippet": parsed.get("snippet") if parsed else "No usable cited valuation.",
            },
            force=force,
        )
        if ok:
            wrote += 1
        else:
            skipped += 1
    return {"wrote": wrote, "skipped": skipped, "searched": searched, "year": year}


def _pick_amount(hits: List[Dict[str, Any]], metric: str) -> Optional[Dict[str, Any]]:
    amounts: List[float] = []
    best: Optional[Dict[str, Any]] = None
    for hit in hits:
        text = " ".join([str(hit.get("title") or ""), str(hit.get("content") or "")])
        for value in parse_usd(text):
            if not in_bounds(metric, value):
                continue
            amounts.append(value)
            if best is None:
                best = {
                    "value": value,
                    "url": hit.get("url"),
                    "title": hit.get("title"),
                    "snippet": (hit.get("content") or "")[:240],
                }
    if len(amounts) >= 2:
        amounts.sort()
        mid = amounts[len(amounts) // 2]
        low, high = amounts[0], amounts[-1]
        if best and high > 0 and (high - low) / high > 0.2:
            best["value"] = mid
            best["status"] = "conflict"
            best["value_low"] = low
            best["value_high"] = high
    return best


def citation_from_row(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    return {
        "status": row.get("status") or "estimate",
        "source_url": row.get("source_url"),
        "source_title": row.get("source_title"),
        "retrieved_at": row.get("retrieved_at"),
        "value_low": row.get("value_low"),
        "value_high": row.get("value_high"),
        "snippet": row.get("snippet"),
    }


def lookup_cap(store: FactStore, year: int) -> float:
    row = store.get("regulation", "fia_cost_cap", year, "budget_cap_usd")
    if row and row.get("value_usd"):
        return float(row["value_usd"])
    return DEFAULT_CAP_USD


TEAM_ALIASES = {
    "mclaren": "mclaren",
    "mclaren formula 1 team": "mclaren",
    "mclaren f1 team": "mclaren",
    "red bull racing": "red bull racing",
    "oracle red bull racing": "red bull racing",
    "red bull": "red bull racing",
    "ferrari": "ferrari",
    "scuderia ferrari": "ferrari",
    "scuderia ferrari hp": "ferrari",
    "mercedes": "mercedes",
    "mercedes-amg petronas": "mercedes",
    "mercedes-amg petronas f1 team": "mercedes",
    "aston martin": "aston martin",
    "aston martin aramco": "aston martin",
    "aston martin aramco f1 team": "aston martin",
    "alpine": "alpine",
    "bwt alpine f1 team": "alpine",
    "williams": "williams",
    "williams racing": "williams",
    "haas": "haas",
    "haas f1 team": "haas",
    "moneygram haas f1 team": "haas",
    "rb": "rb",
    "rb f1 team": "rb",
    "visa cash app rb": "rb",
    "racing bulls": "rb",
    "sauber": "sauber",
    "kick sauber": "sauber",
    "stake f1 team kick sauber": "sauber",
}


def canonical_team(name: str) -> str:
    from app.services.fact_store import normalize_key

    key = normalize_key(name)
    if key in TEAM_ALIASES:
        return TEAM_ALIASES[key]
    for alias, canon in TEAM_ALIASES.items():
        if alias in key or key in alias:
            return canon
    return key


def lookup_valuation(store: FactStore, team_name: str, year: int) -> Optional[Dict[str, Any]]:
    key = canonical_team(team_name)
    row = store.get("constructor", key, year, "valuation_usd")
    if row:
        return row
    row = store.get("constructor", team_name, year, "valuation_usd")
    if row:
        return row
    for fact in store.list_year(year):
        if fact.get("entity_type") != "constructor" or fact.get("metric") != "valuation_usd":
            continue
        if canonical_team(str(fact.get("entity_key") or "")) == key:
            return fact
    return None


def lookup_salary(store: FactStore, driver_number: int, year: int) -> Optional[Dict[str, Any]]:
    return store.get("driver", str(driver_number), year, "salary_usd")
