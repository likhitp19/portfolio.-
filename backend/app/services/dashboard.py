from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import asyncio

from fastapi import HTTPException

from app.config import settings
from app.integrations.jolpica import JolpicaClient
from app.integrations.openf1 import OpenF1Client, OpenF1HTTPError
from app.runtime import get_fact_store
from app.schemas.dashboard import (
    ChampionshipSummary,
    CircuitLabel,
    ConstructorStanding,
    DashboardOverview,
    DriverStanding,
    FactCitation,
    Meeting,
    ProgressionSeries,
    SeasonsResponse,
    StandingsProgression,
    Top3FinishCount,
)
from app.services.commercial import canonical_team, citation_from_row, lookup_salary, lookup_valuation
from app.services.fact_store import DEFAULT_CAP_USD

RACE_POINTS = (25, 18, 15, 12, 10, 8, 6, 4, 2, 1)
TOP_DRIVERS = 5
OPENF1_DETAIL_RACE_CAP = 4

_season_result_cache: Dict[int, List[Dict[str, Any]]] = {}


def last_season_years() -> List[int]:
    end = datetime.now(timezone.utc).year
    count = max(1, int(settings.season_window_years))
    return list(range(end - count + 1, end + 1))


LIVE_LOCK_CODE = "F1_LIVE_LOCK"
LIVE_LOCK_MESSAGE = (
    "OpenF1 has paused public access because an F1 session is on air, including historical "
    "endpoints. This dashboard never requests live data. Wait until the session ends, then refresh."
)


def _http_or_502(exc: OpenF1HTTPError) -> HTTPException:
    message = exc.message or str(exc)
    live_lock = exc.status_code == 401 or "live f1 session" in message.lower()
    if live_lock:
        return HTTPException(
            status_code=503,
            detail={"code": LIVE_LOCK_CODE, "message": LIVE_LOCK_MESSAGE},
        )
    return HTTPException(
        status_code=502,
        detail={"code": "OPENF1_UPSTREAM", "message": str(exc)},
    )


def _is_race(session: Dict[str, Any]) -> bool:
    name = str(session.get("session_name") or "")
    stype = str(session.get("session_type") or "")
    return name == "Race" or stype == "Race"


def _parse_dt(raw: Any) -> Optional[datetime]:
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _is_completed_session(session: Dict[str, Any]) -> bool:
    """Historical races only: session must have ended. Never treat a live GP as latest."""
    now = datetime.now(timezone.utc)
    ended = _parse_dt(session.get("date_end"))
    if ended is not None:
        return ended <= now
    started = _parse_dt(session.get("date_start"))
    if started is None:
        return False
    return started.timestamp() + 3 * 3600 <= now.timestamp()


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def meeting_from_row(row: Dict[str, Any]) -> Meeting:
    return Meeting(
        meeting_key=_as_int(row.get("meeting_key")),
        year=_as_int(row.get("year")),
        meeting_name=str(row.get("meeting_name") or row.get("circuit_short_name") or ""),
        circuit_short_name=str(row.get("circuit_short_name") or ""),
        country_name=str(row.get("country_name") or ""),
        date_start=row.get("date_start"),
    )


def _driver_points(row: Dict[str, Any]) -> float:
    return _as_float(row.get("points_current", row.get("points")))


def _driver_position(row: Dict[str, Any]) -> int:
    return _as_int(row.get("position_current", row.get("position")))


def _driver_name(row: Dict[str, Any], names: Optional[Dict[int, str]] = None) -> str:
    number = _as_int(row.get("driver_number"))
    if names and number in names:
        return names[number]
    return str(row.get("full_name") or row.get("name_acronym") or "Driver {0}".format(number))


def _team_name(row: Dict[str, Any], teams: Optional[Dict[int, str]] = None) -> str:
    number = _as_int(row.get("driver_number"))
    if teams and number in teams:
        return teams[number]
    return str(row.get("team_name") or "")


async def _driver_directory(client: OpenF1Client, session_key: Optional[int]) -> Tuple[Dict[int, str], Dict[int, str]]:
    if not session_key:
        return {}, {}
    rows = await client.get_drivers(session_key=session_key)
    names: Dict[int, str] = {}
    teams: Dict[int, str] = {}
    for row in rows:
        number = _as_int(row.get("driver_number"))
        names[number] = str(row.get("full_name") or row.get("name_acronym") or str(number))
        teams[number] = str(row.get("team_name") or "")
    return names, teams


async def _race_sessions(client: OpenF1Client, year: int, meeting_key: Optional[int] = None) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {"year": year}
    if meeting_key is not None:
        params["meeting_key"] = meeting_key
    sessions = await client.list_sessions(**params)
    races = [s for s in sessions if _is_race(s)]
    races.sort(key=lambda s: str(s.get("date_start") or ""))
    return [s for s in races if _is_completed_session(s)]


async def _standings_from_championship(
    client: OpenF1Client,
    session_key: int,
) -> List[Dict[str, Any]]:
    rows = await client.get_championship_drivers(session_key=session_key)
    if rows:
        return rows
    results = await client.get_session_result(session_key=session_key)
    reconstructed: List[Dict[str, Any]] = []
    for row in results:
        position = _as_int(row.get("position"), 99)
        points = float(RACE_POINTS[position - 1]) if 1 <= position <= 10 else 0.0
        reconstructed.append(
            {
                "driver_number": row.get("driver_number"),
                "position_current": position,
                "points_current": points,
                "team_name": row.get("team_name"),
                "full_name": row.get("full_name"),
            }
        )
    return reconstructed


def _to_driver_standings(
    rows: List[Dict[str, Any]],
    names: Dict[int, str],
    teams: Dict[int, str],
) -> List[DriverStanding]:
    standings = [
        DriverStanding(
            driver_number=_as_int(row.get("driver_number")),
            full_name=_driver_name(row, names),
            team_name=_team_name(row, teams),
            points=_driver_points(row),
            position=_driver_position(row) or 99,
        )
        for row in rows
    ]
    standings.sort(key=lambda item: (item.position, -item.points))
    for index, item in enumerate(standings, start=1):
        if item.position == 99:
            item.position = index
    return standings


async def list_seasons(client: OpenF1Client) -> SeasonsResponse:
    _ = client
    return SeasonsResponse(years=last_season_years())


async def list_meetings(client: OpenF1Client, year: int) -> List[Meeting]:
    try:
        rows = await client.list_meetings(year=year)
    except OpenF1HTTPError as exc:
        if exc.status_code == 401:
            raise _http_or_502(exc)
        rows = []
    if not rows:
        jolpica = JolpicaClient()
        try:
            rows = await jolpica.list_races(year)
        except OpenF1HTTPError as exc:
            raise _http_or_502(exc)
        finally:
            await jolpica.aclose()
    meetings = [meeting_from_row(row) for row in rows]
    meetings.sort(key=lambda m: m.date_start or "")
    return meetings


async def _target_race_session(
    client: OpenF1Client,
    year: int,
    meeting_key: Optional[int],
    session_key: Optional[int],
) -> Optional[int]:
    if session_key:
        return session_key
    races = await _race_sessions(client, year, meeting_key=meeting_key)
    if not races:
        return None
    return _as_int(races[-1].get("session_key")) or None


async def driver_standings(
    client: OpenF1Client,
    year: int,
    meeting_key: Optional[int] = None,
    session_key: Optional[int] = None,
) -> List[DriverStanding]:
    try:
        race_key = await _target_race_session(client, year, meeting_key, session_key)
        if not race_key:
            return []
        names, teams = await _driver_directory(client, race_key)
        rows = await _standings_from_championship(client, race_key)
        standings = _to_driver_standings(rows, names, teams)[:TOP_DRIVERS]
        return _attach_driver_finance(standings, year)
    except OpenF1HTTPError as exc:
        raise _http_or_502(exc)


def _attach_driver_finance(rows: List[DriverStanding], year: int) -> List[DriverStanding]:
    store = get_fact_store()
    enriched: List[DriverStanding] = []
    for row in rows:
        sal = lookup_salary(store, row.driver_number, year)
        salary_usd = float(sal["value_usd"]) if sal and sal.get("value_usd") is not None else None
        fer = (salary_usd / row.points) if salary_usd is not None and row.points else None
        cite = citation_from_row(sal)
        enriched.append(
            DriverStanding(
                driver_number=row.driver_number,
                full_name=row.full_name,
                team_name=row.team_name,
                points=row.points,
                position=row.position,
                salary_usd=salary_usd,
                financial_efficiency=fer,
                salary=FactCitation(**cite) if cite else FactCitation(status="defaulted"),
            )
        )
    return enriched


def _parse_ergast_lap(raw: Any) -> Optional[float]:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        if ":" in text:
            minutes, seconds = text.split(":", 1)
            return float(minutes) * 60.0 + float(seconds)
        return float(text)
    except ValueError:
        return None


def _ergast_classified(status: str) -> bool:
    lowered = (status or "").lower()
    return lowered == "finished" or lowered.startswith("+")


async def _season_results(year: int) -> List[Dict[str, Any]]:
    cached = _season_result_cache.get(year)
    if cached is not None:
        return cached
    jolpica = JolpicaClient()
    try:
        races = await jolpica.list_results(year)
    except OpenF1HTTPError:
        races = []
    finally:
        await jolpica.aclose()
    _season_result_cache[year] = races
    return races


def _wins_from_ergast(races: List[Dict[str, Any]]) -> Dict[str, int]:
    wins: Dict[str, int] = {}
    for race in races:
        for result in race.get("Results") or []:
            if str(result.get("position") or "") != "1":
                continue
            constructor = (result.get("Constructor") or {}).get("name") or ""
            key = canonical_team(str(constructor))
            if key:
                wins[key] = wins.get(key, 0) + 1
    return wins


def _insights_from_ergast(
    races: List[Dict[str, Any]],
) -> Tuple[Optional[str], Optional[float], int, List[Top3FinishCount]]:
    fastest_driver: Optional[str] = None
    fastest_time: Optional[float] = None
    dnf_count = 0
    podiums: Dict[str, int] = {}
    for race in races:
        for result in race.get("Results") or []:
            driver = result.get("Driver") or {}
            name = "{0} {1}".format(driver.get("givenName") or "", driver.get("familyName") or "").strip()
            if not _ergast_classified(str(result.get("status") or "")):
                dnf_count += 1
            position = _as_int(result.get("position"), 99)
            if 1 <= position <= 3 and name:
                podiums[name] = podiums.get(name, 0) + 1
            fastest = result.get("FastestLap") or {}
            if str(fastest.get("rank") or "") != "1":
                continue
            parsed = _parse_ergast_lap((fastest.get("Time") or {}).get("time"))
            if parsed is None:
                continue
            if fastest_time is None or parsed < fastest_time:
                fastest_time = parsed
                fastest_driver = name or None
    top3 = [
        Top3FinishCount(driver_name=name, count=count)
        for name, count in sorted(podiums.items(), key=lambda item: -item[1])[:TOP_DRIVERS]
    ]
    return fastest_driver, fastest_time, dnf_count, top3


async def _constructor_wins(
    client: OpenF1Client,
    year: int,
    meeting_key: Optional[int],
) -> tuple:
    races = await _race_sessions(client, year, meeting_key=meeting_key)
    if meeting_key is None and len(races) > OPENF1_DETAIL_RACE_CAP:
        mapped = _wins_from_ergast(await _season_results(year))
        if mapped:
            return mapped, len(races)
    wins: Dict[str, int] = {}
    for race in races:
        session_key = _as_int(race.get("session_key"))
        if not session_key:
            continue
        names, teams = {}, {}
        results = await client.get_session_result(session_key=session_key)
        for row in results:
            if _as_int(row.get("position"), 99) != 1:
                continue
            team = str(row.get("team_name") or "").strip()
            if not team:
                if not teams:
                    _names, teams = await _driver_directory(client, session_key)
                team = str(_team_name(row, teams) or "").strip()
            if team:
                key = canonical_team(team)
                wins[key] = wins.get(key, 0) + 1
    return wins, len(races)


async def constructor_standings(
    client: OpenF1Client,
    year: int,
    meeting_key: Optional[int] = None,
    session_key: Optional[int] = None,
) -> List[ConstructorStanding]:
    try:
        race_key = await _target_race_session(client, year, meeting_key, session_key)
        if not race_key:
            return []
        teams_rows = await client.get_championship_teams(session_key=race_key)
        wins_map, race_count = await _constructor_wins(client, year, meeting_key)
        if teams_rows:
            result = [
                ConstructorStanding(
                    team_name=str(row.get("team_name") or ""),
                    points=_as_float(row.get("points_current", row.get("points"))),
                    position=_as_int(row.get("position_current", row.get("position"))) or 99,
                )
                for row in teams_rows
            ]
            result.sort(key=lambda item: (item.position, -item.points))
            return _attach_constructor_finance(result, year, wins_map, race_count)
        rows = await _standings_from_championship(client, race_key)
        names, teams = await _driver_directory(client, race_key)
        full = _to_driver_standings(rows, names, teams)
        buckets: Dict[str, float] = {}
        for driver in full:
            buckets[driver.team_name] = buckets.get(driver.team_name, 0.0) + driver.points
        ordered = sorted(buckets.items(), key=lambda pair: -pair[1])
        result = [
            ConstructorStanding(team_name=name, points=points, position=index)
            for index, (name, points) in enumerate(ordered, start=1)
        ]
        return _attach_constructor_finance(result, year, wins_map, race_count)
    except OpenF1HTTPError as exc:
        raise _http_or_502(exc)


def _attach_constructor_finance(
    rows: List[ConstructorStanding],
    year: int,
    wins_map: Dict[str, int],
    race_count: int,
) -> List[ConstructorStanding]:
    store = get_fact_store()
    cap_row = store.get("regulation", "fia_cost_cap", year, "budget_cap_usd")
    cap = float(cap_row["value_usd"]) if cap_row and cap_row.get("value_usd") else DEFAULT_CAP_USD
    cap_cite = citation_from_row(cap_row) or {
        "status": "defaulted",
        "source_title": "Default FIA-style cap",
        "snippet": "USD 135M default when no cited cap is stored.",
    }
    denom = max(race_count, 1)
    enriched: List[ConstructorStanding] = []
    for row in rows:
        wins = wins_map.get(row.team_name, 0) or wins_map.get(canonical_team(row.team_name), 0)
        val_row = lookup_valuation(store, row.team_name, year)
        cpp = (cap / row.points) if row.points else None
        enriched.append(
            ConstructorStanding(
                team_name=row.team_name,
                points=row.points,
                position=row.position,
                valuation_usd=float(val_row["value_usd"]) if val_row and val_row.get("value_usd") is not None else None,
                budget_cap_usd=cap,
                cost_per_point=cpp,
                wins=wins,
                avg_wins=wins / denom,
                valuation=FactCitation(**citation_from_row(val_row)) if val_row else FactCitation(status="defaulted"),
                budget_cap=FactCitation(**cap_cite),
            )
        )
    return enriched


def _row_dnf(row: Dict[str, Any]) -> bool:
    for key in ("dnf", "dns", "dsq", "retired"):
        value = row.get(key)
        if value is True or value == 1 or str(value).lower() in {"true", "1", "yes"}:
            return True
    status = str(row.get("status") or row.get("classified") or "").lower()
    if any(token in status for token in ("dnf", "retired", "accident", "lapped out", "did not finish")):
        return True
    position = row.get("position")
    if position in {None, "", 0} and row.get("dnf") is not False:
        laps = _as_int(row.get("number_of_laps") or row.get("laps"), 0)
        if laps and laps < 3:
            return True
    return False


async def _insights_for_races(
    client: OpenF1Client,
    races: List[Dict[str, Any]],
    names: Dict[int, str],
) -> Tuple[Optional[str], Optional[float], int, List[Top3FinishCount]]:
    fastest_driver: Optional[str] = None
    fastest_time: Optional[float] = None
    dnf_count = 0
    podiums: Dict[int, int] = {}
    for race in races:
        session_key = _as_int(race.get("session_key"))
        if not session_key:
            continue
        results = await client.get_session_result(session_key=session_key)
        for row in results:
            number = _as_int(row.get("driver_number"))
            if row.get("full_name"):
                names[number] = str(row.get("full_name"))
            if _row_dnf(row):
                dnf_count += 1
            position = _as_int(row.get("position"), 99)
            if 1 <= position <= 3:
                podiums[number] = podiums.get(number, 0) + 1
    if races:
        last_key = _as_int(races[-1].get("session_key"))
        if last_key:
            try:
                laps = await asyncio.wait_for(client.get_laps(session_key=last_key), timeout=8)
            except (asyncio.TimeoutError, OpenF1HTTPError):
                laps = []
            for lap in laps:
                duration = lap.get("lap_duration") if lap.get("lap_duration") is not None else lap.get("duration")
                if duration is None:
                    continue
                value = _as_float(duration, default=-1)
                if value <= 0:
                    continue
                if fastest_time is None or value < fastest_time:
                    fastest_time = value
                    fastest_driver = _driver_name(lap, names)
    top3 = [
        Top3FinishCount(driver_name=names.get(number, "Driver {0}".format(number)), count=count)
        for number, count in sorted(podiums.items(), key=lambda item: -item[1])[:TOP_DRIVERS]
    ]
    return fastest_driver, fastest_time, dnf_count, top3


async def championship_summary(
    client: OpenF1Client,
    year: int,
    meeting_key: Optional[int] = None,
) -> ChampionshipSummary:
    drivers = await driver_standings(client, year, meeting_key)
    try:
        races = await _race_sessions(client, year, meeting_key=meeting_key)
    except OpenF1HTTPError as exc:
        raise _http_or_502(exc)
    names: Dict[int, str] = {}
    if races:
        names, _teams = await _driver_directory(client, _as_int(races[-1].get("session_key")))
    try:
        if meeting_key is None and len(races) > OPENF1_DETAIL_RACE_CAP:
            fastest_driver, fastest_time, dnf_count, top3 = _insights_from_ergast(await _season_results(year))
            if fastest_driver is None and dnf_count == 0:
                fastest_driver, fastest_time, dnf_count, top3 = await _insights_for_races(
                    client, races[-1:], names
                )
        else:
            fastest_driver, fastest_time, dnf_count, top3 = await _insights_for_races(client, races, names)
    except OpenF1HTTPError as exc:
        raise _http_or_502(exc)
    if not drivers:
        return ChampionshipSummary(
            race_count=len(races),
            fastest_lap_driver=fastest_driver,
            fastest_lap_duration=fastest_time,
            total_dnfs=dnf_count,
            top3_finishes=top3,
        )
    leader = drivers[0]
    gap = None
    if len(drivers) > 1:
        gap = leader.points - drivers[1].points
    return ChampionshipSummary(
        leader_name=leader.full_name,
        leader_points=leader.points,
        points_gap=gap,
        race_count=len(races),
        fastest_lap_driver=fastest_driver,
        fastest_lap_duration=fastest_time,
        total_dnfs=dnf_count,
        top3_finishes=top3,
    )


async def _progression_pair(
    client: OpenF1Client, year: int
) -> Tuple[StandingsProgression, StandingsProgression]:
    try:
        meetings = await list_meetings(client, year)
        races = await _race_sessions(client, year)
        bulk = await client.get_championship_drivers(year=year)
    except OpenF1HTTPError as exc:
        raise _http_or_502(exc)
    by_session: Dict[int, List[Dict[str, Any]]] = {}
    for row in bulk:
        session_key = _as_int(row.get("session_key"))
        if session_key:
            by_session.setdefault(session_key, []).append(row)
    race_by_meeting = {_as_int(r.get("meeting_key")): r for r in races}
    last_race = races[-1] if races else None
    names, teams = {}, {}
    if last_race:
        names, teams = await _driver_directory(client, _as_int(last_race.get("session_key")))
    circuits: List[CircuitLabel] = []
    snapshots: List[List[DriverStanding]] = []
    for meeting in meetings:
        race = race_by_meeting.get(meeting.meeting_key)
        if not race:
            continue
        session_key = _as_int(race.get("session_key"))
        rows = by_session.get(session_key)
        if not rows:
            try:
                rows = await _standings_from_championship(client, session_key)
            except OpenF1HTTPError as exc:
                raise _http_or_502(exc)
        circuits.append(
            CircuitLabel(
                meeting_key=meeting.meeting_key,
                name=meeting.circuit_short_name or meeting.meeting_name,
            )
        )
        snapshots.append(_to_driver_standings(rows, names, teams))
    if not snapshots:
        empty = StandingsProgression()
        return empty, empty
    latest = {d.driver_number: d for d in snapshots[-1]}
    top = sorted(latest.values(), key=lambda d: (d.position, -d.points))[:TOP_DRIVERS]
    series: List[ProgressionSeries] = []
    for driver in top:
        points_over_time: List[float] = []
        running = 0.0
        for snapshot in snapshots:
            found = next((d for d in snapshot if d.driver_number == driver.driver_number), None)
            if found:
                running = found.points
            points_over_time.append(running)
        series.append(ProgressionSeries(driver=driver.full_name, points=points_over_time))
    constructor_series: List[ProgressionSeries] = []
    latest_teams: Dict[str, float] = {}
    for driver in snapshots[-1]:
        latest_teams[driver.team_name] = latest_teams.get(driver.team_name, 0.0) + driver.points
    top_teams = sorted(latest_teams.items(), key=lambda item: -item[1])[:TOP_DRIVERS]
    for team_name, _pts in top_teams:
        points_over_time = [
            sum(d.points for d in snapshot if d.team_name == team_name) for snapshot in snapshots
        ]
        constructor_series.append(ProgressionSeries(driver=team_name, points=points_over_time))
    return (
        StandingsProgression(circuits=circuits, series=series),
        StandingsProgression(circuits=circuits, series=constructor_series),
    )


async def standings_progression(client: OpenF1Client, year: int) -> StandingsProgression:
    driver_prog, _constructor_prog = await _progression_pair(client, year)
    return driver_prog


def _manufacturer_story(constructors: List[ConstructorStanding]) -> Tuple[Optional[str], Optional[str]]:
    if not constructors:
        return None, None
    efficient = [row for row in constructors if row.cost_per_point and row.points > 0]
    winner = max(constructors, key=lambda row: (row.wins, row.points))
    if efficient:
        best = min(efficient, key=lambda row: row.cost_per_point or 10**18)
        reason = (
            "{0} is the efficiency pick: ${1:,.0f} per point against the stored cap, "
            "{2:.0f} pts and {3} wins. {4} still banks the most race wins ({5})."
        ).format(
            best.team_name,
            best.cost_per_point or 0,
            best.points,
            best.wins,
            winner.team_name,
            winner.wins,
        )
        return best.team_name, reason
    leader = constructors[0]
    return leader.team_name, "{0} leads on points ({1:.0f}). Cost-per-point needs stored commercial facts.".format(
        leader.team_name, leader.points
    )


async def dashboard_overview(
    client: OpenF1Client,
    year: int,
    meeting_key: Optional[int] = None,
) -> DashboardOverview:
    seasons = await list_seasons(client)
    meetings = await list_meetings(client, year)
    drivers = await driver_standings(client, year, meeting_key)
    constructors = await constructor_standings(client, year, meeting_key)
    summary = await championship_summary(client, year, meeting_key)
    driver_prog, constructor_prog = await _progression_pair(client, year)
    best_name, best_reason = _manufacturer_story(constructors)
    summary.best_manufacturer = best_name
    summary.best_manufacturer_reason = best_reason
    return DashboardOverview(
        year=year,
        meeting_key=meeting_key,
        years=seasons.years,
        meetings=meetings,
        drivers=drivers,
        constructors=constructors,
        summary=summary,
        progression=driver_prog,
        constructor_progression=constructor_prog,
    )

