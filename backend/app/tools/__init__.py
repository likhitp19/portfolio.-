"""OpenF1 tools for the Protest Engine context pack.

Path note: brief asked for ``backend/tools/openf1.py``; this repo packages
code under ``backend/app/``, so the import path is ``app.tools.openf1``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.integrations.openf1 import OpenF1Client, OpenF1HTTPError
from app.runtime import get_client


def _client(openf1: Optional[OpenF1Client] = None) -> OpenF1Client:
    if openf1 is not None:
        return openf1
    return get_client()


async def fetch_race_control(
    *,
    session_key: int,
    openf1: Optional[OpenF1Client] = None,
    limit: int = 40,
) -> List[Dict[str, Any]]:
    """Fetch `/v1/race_control` messages for session status and incident notes."""
    client = _client(openf1)
    try:
        rows = await client.get_race_control(session_key=session_key)
    except OpenF1HTTPError:
        return []
    cleaned: List[Dict[str, Any]] = []
    for row in rows or []:
        cleaned.append(
            {
                "date": row.get("date"),
                "category": row.get("category"),
                "flag": row.get("flag"),
                "message": row.get("message"),
                "scope": row.get("scope"),
                "sector": row.get("sector"),
                "driver_number": row.get("driver_number"),
                "lap_number": row.get("lap_number"),
            }
        )
    return cleaned[:limit]


async def fetch_team_radio(
    *,
    session_key: int,
    driver_numbers: Optional[List[int]] = None,
    openf1: Optional[OpenF1Client] = None,
    limit: int = 30,
) -> List[Dict[str, Any]]:
    """Fetch `/v1/team_radio` driver-to-pit communications for involved cars."""
    client = _client(openf1)
    wanted = set(int(n) for n in (driver_numbers or []) if n is not None)
    try:
        rows = await client.get_team_radio(session_key=session_key)
    except OpenF1HTTPError:
        return []
    cleaned: List[Dict[str, Any]] = []
    for row in rows or []:
        number = row.get("driver_number")
        if wanted and number not in wanted and str(number) not in {str(n) for n in wanted}:
            continue
        cleaned.append(
            {
                "date": row.get("date"),
                "driver_number": number,
                "recording_url": row.get("recording_url"),
                "meeting_key": row.get("meeting_key"),
                "session_key": row.get("session_key"),
            }
        )
    return cleaned[:limit]


def summarize_race_control(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return "Race control: no messages returned for this session window."
    lines = []
    for row in rows[:12]:
        stamp = row.get("date") or "?"
        cat = row.get("category") or "Message"
        msg = row.get("message") or ""
        lines.append("[{0}] {1}: {2}".format(stamp, cat, msg))
    return "Race control ({0} msgs): {1}".format(len(rows), " | ".join(lines))


def summarize_team_radio(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return "Team radio: no recordings returned for involved drivers."
    lines = []
    for row in rows[:10]:
        lines.append(
            "Driver {0} @ {1} ({2})".format(
                row.get("driver_number"),
                row.get("date") or "?",
                row.get("recording_url") or "no url",
            )
        )
    return "Team radio ({0}): {1}".format(len(rows), " | ".join(lines))
