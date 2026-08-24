from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.integrations.jolpica import JolpicaClient
from app.integrations.openf1 import OpenF1HTTPError
from app.schemas.analytics import (
    ConstructorTimeline,
    ConstructorTimelineSeries,
    RegulatoryEra,
    TeammateDeltaMatrix,
    TeammateDeltaRow,
)
from app.services.lineage import (
    GRID_LINEAGE_IDS,
    constructor_lineage_id,
    display_name_for,
)

REGULATORY_ERAS = [
    RegulatoryEra(id="turbo_hybrid", label="Turbo-Hybrid", start_year=2014, end_year=2021),
    RegulatoryEra(id="ground_effect", label="Ground Effect", start_year=2022, end_year=2025),
    RegulatoryEra(id="active_aero", label="Active Aero & 50/50 Power", start_year=2026, end_year=2030),
]

SHARE_RISK_PCT = 62.0
QUALI_RISK_MS = 200.0

_timeline_cache: Dict[Tuple[int, int], Tuple[float, ConstructorTimeline]] = {}
_teammate_cache: Dict[int, Tuple[float, TeammateDeltaMatrix]] = {}
_TTL_SECONDS = 900.0


def clear_analytics_cache() -> None:
    _timeline_cache.clear()
    _teammate_cache.clear()


def parse_lap_ms(raw: Any) -> Optional[float]:
    text = str(raw or "").strip()
    if not text or text in {"\\N", "null"}:
        return None
    try:
        if ":" in text:
            minutes, seconds = text.split(":", 1)
            return round((float(minutes) * 60.0 + float(seconds)) * 1000.0, 3)
        return round(float(text) * 1000.0, 3)
    except ValueError:
        return None


def same_session_quali_ms(left: Dict[str, Any], right: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    for key in ("Q3", "Q2", "Q1"):
        first = parse_lap_ms(left.get(key))
        second = parse_lap_ms(right.get(key))
        if first is not None and second is not None:
            return first, second
    return None


def classify_quadrant(dominant_share_pct: float, quali_ms: Optional[float]) -> str:
    high_share = dominant_share_pct >= SHARE_RISK_PCT
    high_delta = quali_ms is not None and quali_ms >= QUALI_RISK_MS
    if high_share and high_delta:
        return "high_asset_risk"
    if not high_share and (quali_ms is None or quali_ms < QUALI_RISK_MS):
        return "balanced_portfolio"
    return "watch"


def pair_teammates(drivers: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, Any], str, str]]:
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    names: Dict[str, str] = {}
    for row in drivers:
        lineage = constructor_lineage_id(str(row.get("constructor_id") or ""), str(row.get("team_name") or ""))
        if not lineage:
            continue
        buckets.setdefault(lineage, []).append(row)
        names[lineage] = str(row.get("team_name") or names.get(lineage) or lineage)
    pairs: List[Tuple[Dict[str, Any], Dict[str, Any], str, str]] = []
    for lineage, members in buckets.items():
        ranked = sorted(members, key=lambda item: -float(item.get("points") or 0))
        if len(ranked) < 2:
            continue
        pairs.append((ranked[0], ranked[1], lineage, names.get(lineage, lineage)))
    return pairs


def quali_gaps_by_constructor(races: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    gaps: Dict[str, List[float]] = {}
    for race in races:
        by_team: Dict[str, List[Dict[str, Any]]] = {}
        for result in race.get("QualifyingResults") or []:
            constructor = result.get("Constructor") or {}
            lineage = constructor_lineage_id(
                str(constructor.get("constructorId") or ""),
                str(constructor.get("name") or ""),
            )
            if not lineage:
                continue
            by_team.setdefault(lineage, []).append(result)
        for lineage, entries in by_team.items():
            if len(entries) < 2:
                continue
            pair = same_session_quali_ms(entries[0], entries[1])
            if pair is None:
                continue
            gaps.setdefault(lineage, []).append(abs(pair[0] - pair[1]))
    return gaps


def signed_quali_delta(
    races: List[Dict[str, Any]],
    constructor_id: str,
    driver_a: str,
    driver_b: str,
) -> Tuple[Optional[float], int]:
    deltas: List[float] = []
    a_key = driver_a.lower()
    b_key = driver_b.lower()
    for race in races:
        times: Dict[str, Dict[str, Any]] = {}
        for result in race.get("QualifyingResults") or []:
            constructor = result.get("Constructor") or {}
            lineage = constructor_lineage_id(
                str(constructor.get("constructorId") or ""),
                str(constructor.get("name") or ""),
            )
            if lineage != constructor_id:
                continue
            driver = result.get("Driver") or {}
            name = ("{0} {1}".format(driver.get("givenName") or "", driver.get("familyName") or "")).strip().lower()
            times[name] = result
        if a_key in times and b_key in times:
            pair = same_session_quali_ms(times[a_key], times[b_key])
            if pair is not None:
                deltas.append(pair[0] - pair[1])
    if not deltas:
        return None, 0
    return sum(deltas) / len(deltas), len(deltas)


async def _standings_year(year: int) -> List[Dict[str, Any]]:
    jolpica = JolpicaClient()
    try:
        return await jolpica.constructor_standings(year)
    except OpenF1HTTPError:
        return []
    finally:
        await jolpica.aclose()


async def constructor_timeline(from_year: int = 2014, to_year: Optional[int] = None) -> ConstructorTimeline:
    end = to_year or datetime.now(timezone.utc).year
    start = min(from_year, end)
    cache_key = (start, end)
    cached = _timeline_cache.get(cache_key)
    now = time.monotonic()
    if cached and now - cached[0] < _TTL_SECONDS:
        return cached[1]

    years = list(range(start, end + 1))
    semaphore = asyncio.Semaphore(4)

    async def one(year: int) -> Tuple[int, List[Dict[str, Any]]]:
        async with semaphore:
            return year, await _standings_year(year)

    fetched = await asyncio.gather(*[one(year) for year in years])
    by_year = {year: rows for year, rows in fetched}

    series: List[ConstructorTimelineSeries] = []
    for lineage_id in GRID_LINEAGE_IDS:
        points: List[Optional[float]] = []
        positions: List[Optional[int]] = []
        label = display_name_for(lineage_id)
        for year in years:
            match = None
            for row in by_year.get(year) or []:
                if constructor_lineage_id(str(row.get("constructor_id") or ""), str(row.get("team_name") or "")) == lineage_id:
                    match = row
                    label = display_name_for(lineage_id, str(row.get("team_name") or label))
                    break
            if match:
                points.append(float(match.get("points") or 0))
                positions.append(int(match.get("position") or 0) or None)
            else:
                points.append(None)
                positions.append(None)
        if any(value is not None for value in points):
            series.append(
                ConstructorTimelineSeries(
                    constructor_id=lineage_id,
                    display_name=label,
                    points=points,
                    positions=positions,
                )
            )

    payload = ConstructorTimeline(
        from_year=start,
        to_year=end,
        years=years,
        series=series,
        eras=list(REGULATORY_ERAS),
        source="jolpica",
    )
    _timeline_cache[cache_key] = (now, payload)
    return payload


async def teammate_delta_matrix(year: int) -> TeammateDeltaMatrix:
    cached = _teammate_cache.get(year)
    now = time.monotonic()
    if cached and now - cached[0] < _TTL_SECONDS:
        return cached[1]

    jolpica = JolpicaClient()
    try:
        drivers = await jolpica.driver_standings(year)
        races = await jolpica.list_qualifying(year)
    except OpenF1HTTPError:
        drivers, races = [], []
    finally:
        await jolpica.aclose()

    rows: List[TeammateDeltaRow] = []
    for driver_a, driver_b, lineage, team_name in pair_teammates(drivers):
        points_a = float(driver_a.get("points") or 0)
        points_b = float(driver_b.get("points") or 0)
        total = points_a + points_b
        share = (points_a / total * 100.0) if total else 50.0
        dominant = max(points_a, points_b) / total * 100.0 if total else 50.0
        signed, sample = signed_quali_delta(
            races,
            lineage,
            str(driver_a.get("full_name") or ""),
            str(driver_b.get("full_name") or ""),
        )
        abs_ms = abs(signed) if signed is not None else None
        rows.append(
            TeammateDeltaRow(
                constructor_id=lineage,
                team_name=team_name,
                driver_a_name=str(driver_a.get("full_name") or ""),
                driver_b_name=str(driver_b.get("full_name") or ""),
                points_a=points_a,
                points_b=points_b,
                points_share_pct=round(share, 1),
                dominant_share_pct=round(dominant, 1),
                quali_pace_delta_ms=round(abs_ms, 1) if abs_ms is not None else None,
                signed_delta_ms=round(signed, 1) if signed is not None else None,
                sample_races=sample,
                quadrant=classify_quadrant(dominant, abs_ms),
            )
        )
    rows.sort(key=lambda item: -item.dominant_share_pct)
    payload = TeammateDeltaMatrix(
        year=year,
        rows=rows,
        share_risk_pct=SHARE_RISK_PCT,
        quali_risk_ms=QUALI_RISK_MS,
        source="jolpica",
    )
    _teammate_cache[year] = (now, payload)
    return payload
