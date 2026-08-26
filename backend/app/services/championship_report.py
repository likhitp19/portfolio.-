from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

POINTS_PER_RACE_MAX = 26
DEFAULT_SEASON_RACES = 24


def _rows(grouped: Dict[str, List[Dict[str, Any]]], tool: str) -> List[Dict[str, Any]]:
    payloads = grouped.get(tool) or []
    if not payloads:
        return []
    return list(payloads[-1].get("preview") or [])


def _all_result_rows(grouped: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for payload in grouped.get("get_session_result") or []:
        rows.extend(list(payload.get("preview") or []))
    return rows


def _driver_directory(
    grouped: Dict[str, List[Dict[str, Any]]],
) -> Tuple[Dict[str, str], Dict[str, str]]:
    names: Dict[str, str] = {}
    teams: Dict[str, str] = {}
    for tool in ("get_drivers", "get_championship_drivers", "get_session_result"):
        payloads = grouped.get(tool) or []
        for payload in payloads:
            for row in payload.get("preview") or []:
                key = str(row.get("driver_number") or "")
                label = str(
                    row.get("full_name")
                    or row.get("broadcast_name")
                    or " ".join(part for part in (row.get("first_name"), row.get("last_name")) if part)
                    or row.get("name_acronym")
                    or ""
                ).strip()
                if key and label and not label.isdigit():
                    names[key] = label
                team = str(
                    row.get("team_name") or row.get("constructor_name") or ""
                ).strip()
                if key and team and team != "—":
                    teams[key] = team
    return names, teams


def _name(row: Dict[str, Any], names: Optional[Dict[str, str]] = None) -> str:
    key = str(row.get("driver_number") or "")
    mapped = (names or {}).get(key)
    if mapped:
        return mapped
    label = str(
        row.get("full_name")
        or row.get("broadcast_name")
        or " ".join(part for part in (row.get("first_name"), row.get("last_name")) if part)
        or row.get("name_acronym")
        or ""
    ).strip()
    if label and not label.isdigit():
        return label
    return label or key or "Unknown"


def _headshots(grouped: Dict[str, List[Dict[str, Any]]]) -> Dict[str, str]:
    shots: Dict[str, str] = {}
    for payload in grouped.get("get_drivers") or []:
        for row in payload.get("preview") or []:
            key = str(row.get("driver_number") or "")
            url = str(row.get("headshot_url") or "").strip()
            if key and url:
                shots[key] = url
    return shots


def _contenders(
    drivers: List[Dict[str, Any]],
    names: Dict[str, str],
    shots: Dict[str, str],
    teams: Dict[str, str],
) -> List[Dict[str, Any]]:
    cards = []
    for index, row in enumerate(drivers[:4], start=1):
        key = str(row.get("driver_number") or "")
        cards.append(
            {
                "driver_number": key,
                "full_name": _name(row, names),
                "team_name": _team(row, teams),
                "points": _pts(row),
                "position": int(row.get("position_current") or row.get("position") or index),
                "headshot_url": shots.get(key) or None,
            }
        )
    return cards


def _pts(row: Dict[str, Any]) -> float:
    raw = row.get("points_current", row.get("points"))
    try:
        return float(raw or 0)
    except (TypeError, ValueError):
        return 0.0


def _team(row: Dict[str, Any], teams: Optional[Dict[str, str]] = None) -> str:
    key = str(row.get("driver_number") or "")
    mapped = (teams or {}).get(key)
    if mapped:
        return mapped
    return str(row.get("team_name") or row.get("constructor_name") or "—")


def _is_dnf(row: Dict[str, Any]) -> bool:
    flag = row.get("dnf")
    if flag is True or str(flag).lower() in {"true", "1", "yes"}:
        return True
    pos = str(row.get("position") or "").upper()
    return pos in {"DNF", "DNS", "DSQ", "NC"}


def _races_from_sessions(sessions: List[Dict[str, Any]], now: datetime) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    races = [
        row
        for row in sessions
        if str(row.get("session_name") or row.get("session_type") or "") == "Race"
    ]
    races.sort(key=lambda row: str(row.get("date_start") or ""))
    completed: List[Dict[str, Any]] = []
    remaining: List[Dict[str, Any]] = []
    for race in races:
        stamp = str(race.get("date_start") or "")
        try:
            when = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        except ValueError:
            completed.append(race)
            continue
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        if when <= now:
            completed.append(race)
        else:
            remaining.append(race)
    return completed, remaining


def _form_table(
    results: List[Dict[str, Any]],
    drivers: List[Dict[str, Any]],
    names: Dict[str, str],
    teams: Dict[str, str],
) -> List[Dict[str, Any]]:
    by_driver: Dict[str, List[int]] = {}
    wins: Dict[str, int] = {}
    dnfs: Dict[str, int] = {}
    starts: Dict[str, int] = {}
    for row in results:
        key = str(row.get("driver_number") or _name(row, names))
        starts[key] = starts.get(key, 0) + 1
        try:
            position = int(row.get("position") or 99)
        except (TypeError, ValueError):
            position = 99
        by_driver.setdefault(key, []).append(position)
        if position == 1:
            wins[key] = wins.get(key, 0) + 1
        if _is_dnf(row):
            dnfs[key] = dnfs.get(key, 0) + 1
    ranked = []
    for row in drivers[:8]:
        key = str(row.get("driver_number") or _name(row, names))
        finishes = by_driver.get(key) or []
        start_n = starts.get(key) or 0
        ranked.append(
            {
                "name": _name(row, names),
                "team": _team(row, teams),
                "points": _pts(row),
                "recent": ", ".join("P{0}".format(pos) if pos < 90 else "DNF" for pos in finishes[-5:]) or "—",
                "wins": wins.get(key, 0),
                "win_rate": round(100.0 * wins.get(key, 0) / start_n, 1) if start_n else 0.0,
                "dnfs": dnfs.get(key, 0),
                "starts": start_n,
            }
        )
    return ranked


def _confidence(leader_pts: float, second_pts: float, remaining: int, leader_form: Dict[str, Any]) -> float:
    gap = leader_pts - second_pts
    ceiling = max(remaining, 0) * POINTS_PER_RACE_MAX
    if remaining <= 0:
        return 0.99 if gap > 0 else 0.5
    if gap >= ceiling:
        return 0.97
    share = gap / max(ceiling, 1)
    form = 0.0
    if leader_form.get("starts"):
        form = min(0.12, (leader_form.get("wins") or 0) / max(leader_form.get("starts"), 1) * 0.2)
    reliability = 0.0
    starts = leader_form.get("starts") or 0
    if starts:
        reliability = -min(0.1, (leader_form.get("dnfs") or 0) / starts * 0.25)
    return round(min(0.96, max(0.51, 0.55 + share * 0.4 + form + reliability)), 2)


def build_championship_report(
    grouped: Dict[str, List[Dict[str, Any]]],
    year: Optional[int],
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    drivers = list(_rows(grouped, "get_championship_drivers"))
    names, teams = _driver_directory(grouped)
    shots = _headshots(grouped)
    drivers.sort(key=lambda row: int(row.get("position_current") or row.get("position") or 99))
    constructors = list(_rows(grouped, "get_championship_teams"))
    constructors.sort(key=lambda row: int(row.get("position") or row.get("position_current") or 99))
    sessions = _rows(grouped, "list_sessions")
    completed, remaining_sessions = _races_from_sessions(sessions, now)
    remaining_n = len(remaining_sessions) if sessions else DEFAULT_SEASON_RACES
    results = _all_result_rows(grouped)
    form = _form_table(results, drivers, names, teams)
    leader = drivers[0] if drivers else {}
    second = drivers[1] if len(drivers) > 1 else {}
    leader_form = form[0] if form else {}
    confidence = _confidence(_pts(leader), _pts(second), remaining_n, leader_form) if leader else 0.0
    winner = _name(leader, names) if leader else "Insufficient standings"
    gap = _pts(leader) - _pts(second) if leader and second else 0.0
    key_drivers = []
    if leader and second:
        key_drivers.append(
            "{0} leads {1} by {2:.0f} pts with {3} race(s) still scoring (max {4} pts/weekend).".format(
                winner, _name(second, names), gap, remaining_n, POINTS_PER_RACE_MAX
            )
        )
    if leader_form:
        key_drivers.append(
            "Sampled classifications: {0} wins / {1} DNFs across {2} starts in the retrieved race files.".format(
                leader_form.get("wins") or 0,
                leader_form.get("dnfs") or 0,
                leader_form.get("starts") or 0,
            )
        )
    if len(key_drivers) < 2:
        key_drivers.append("Projection uses live OpenF1/Jolpica standings and race classifications — not a cached narrative.")

    teammate_rows = []
    by_team: Dict[str, List[Dict[str, Any]]] = {}
    for row in drivers:
        by_team.setdefault(_team(row, teams), []).append(row)
    for team, members in by_team.items():
        if team == "—" or len(members) < 2:
            continue
        members = sorted(members, key=_pts, reverse=True)
        lead, chase = members[0], members[1]
        teammate_rows.append(
            {
                "team": team,
                "lead": _name(lead, names),
                "chase": _name(chase, names),
                "cushion": round(_pts(lead) - _pts(chase), 1),
            }
        )
    teammate_rows.sort(key=lambda item: item["cushion"], reverse=True)

    remaining_names = [
        str(row.get("circuit_short_name") or row.get("session_name") or row.get("country_name") or "TBD")
        for row in remaining_sessions[:8]
    ]

    citations = []
    for tool in ("list_sessions", "get_championship_drivers", "get_championship_teams", "get_session_result", "get_laps", "get_drivers"):
        for payload in grouped.get(tool) or []:
            citations.append(
                {
                    "tool": tool,
                    "rows": payload.get("record_count") or len(payload.get("preview") or []),
                    "status": payload.get("status") or "ok",
                }
            )

    pace_md = [
        "| Driver | Team | Pts | Recent finishes | Wins (sample) | Win rate |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in form[:8]:
        pace_md.append(
            "| {0} | {1} | {2:.0f} | {3} | {4} | {5}% |".format(
                row["name"], row["team"], row["points"], row["recent"], row["wins"], row["win_rate"]
            )
        )

    reliability_md = [
        "| Driver | Starts sampled | DNFs | DNF % |",
        "| --- | --- | --- | --- |",
    ]
    for row in form[:8]:
        pct = round(100.0 * row["dnfs"] / row["starts"], 1) if row["starts"] else 0.0
        reliability_md.append("| {0} | {1} | {2} | {3}% |".format(row["name"], row["starts"], row["dnfs"], pct))

    constructor_md = [
        "| Constructor | Pts | Position |",
        "| --- | --- | --- |",
    ]
    for row in constructors[:10]:
        constructor_md.append(
            "| {0} | {1:.0f} | {2} |".format(
                row.get("team_name") or row.get("name") or "—",
                _pts(row),
                row.get("position") or row.get("position_current") or "—",
            )
        )

    teammate_md = [
        "| Constructor | Lead asset | Teammate | Point cushion |",
        "| --- | --- | --- | --- |",
    ]
    for row in teammate_rows[:8]:
        teammate_md.append(
            "| {0} | {1} | {2} | {3:.0f} |".format(row["team"], row["lead"], row["chase"], row["cushion"])
        )

    cites_md = [
        "| Source tool | Rows | Status |",
        "| --- | --- | --- |",
    ]
    for row in citations:
        cites_md.append("| `{0}` | {1} | {2} |".format(row["tool"], row["rows"], row["status"]))

    tracks = ", ".join(remaining_names) if remaining_names else "calendar remainder inferred from completed Race sessions"
    deep = "\n\n".join(
        [
            "## Pace & Trajectory Analysis",
            "\n".join(pace_md) if len(pace_md) > 2 else "No race classifications were returned for form sampling.",
            "## Car Reliability & DNF Impact",
            "\n".join(reliability_md) if len(reliability_md) > 2 else "No DNF flags in retrieved session_result files.",
            "## Remaining Track Suitability & Constructor Efficiency",
            "Remaining / unscored weekends: {0}.".format(tracks),
            "\n".join(constructor_md) if len(constructor_md) > 2 else "Constructor standings were empty.",
            "## Teammate Delta & Point Cushion",
            "\n".join(teammate_md) if len(teammate_md) > 2 else "Could not pair teammates from standings.",
            "## Data Citations & Sources",
            "Season {0}. OpenF1 `GET /v1/drivers` (headshot_url), `/v1/sessions`, `/v1/championship_drivers`, `/v1/championship_teams`, `/v1/session_result`, `/v1/laps`.".format(
                year or "current"
            ),
            "\n".join(cites_md),
        ]
    )
    summary = (
        "{0} is the projected Drivers' Champion for {1} at {2:.0f}% confidence. "
        "{3}"
    ).format(winner, year or "this season", confidence * 100, key_drivers[0] if key_drivers else "")
    answer = "## Executive TL;DR\n\n{0}\n\n## In-Depth Research Report\n\n{1}".format(summary, deep)
    follow_ups = [
        "How would a DNF for {0} change the title math?".format(winner),
        "Which remaining circuits favor {0}'s constructor?".format(winner),
        "How large is the teammate point cushion in the lead garage?",
    ]
    return {
        "answer": answer,
        "predicted_winner": winner,
        "confidence": confidence,
        "key_drivers": key_drivers[:2],
        "contenders": _contenders(drivers, names, shots, teams),
        "follow_ups": follow_ups,
        "year": year,
        "remaining_races": remaining_n,
        "leader_points": _pts(leader) if leader else 0,
        "second_points": _pts(second) if second else 0,
    }
