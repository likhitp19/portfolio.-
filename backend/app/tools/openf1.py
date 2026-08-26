"""OpenF1 tools for the Protest Engine context pack.

Brief path ``backend/tools/openf1.py`` maps to ``app.tools.openf1``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.integrations.openf1 import OpenF1HTTPError
from app.runtime import get_client


def _client(openf1: Optional[Any] = None) -> Any:
    if openf1 is not None:
        return openf1
    return get_client()


async def get_race_control(
    session_key: int,
    lap_number: Optional[int] = None,
    *,
    openf1: Optional[Any] = None,
    limit: int = 40,
) -> List[Dict[str, Any]]:
    """Fetch `/v1/race_control` flags, incident notes, and investigation messages.

    Graceful fallback: empty list on HTTP errors / empty payloads (including 401).
    """
    client = _client(openf1)
    try:
        rows = await client.get_race_control(session_key=session_key)
    except OpenF1HTTPError:
        return []
    except Exception:
        return []

    cleaned: List[Dict[str, Any]] = []
    for row in rows or []:
        row_lap = row.get("lap_number")
        if lap_number is not None and row_lap is not None:
            try:
                if int(row_lap) != int(lap_number):
                    continue
            except (TypeError, ValueError):
                pass
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
    # If lap filter emptied the pack, fall back to full session window (coarse context).
    if lap_number is not None and not cleaned and rows:
        return await get_race_control(session_key, None, openf1=openf1, limit=limit)
    return cleaned[:limit]


async def get_team_radio(
    session_key: int,
    driver_number: int,
    *,
    openf1: Optional[Any] = None,
    limit: int = 30,
) -> List[Dict[str, Any]]:
    """Fetch `/v1/team_radio` driver-to-pit metadata / transcript references.

    Graceful fallback: empty list on HTTP errors / empty payloads (including 401).
    """
    client = _client(openf1)
    try:
        rows = await client.get_team_radio(session_key=session_key, driver_number=driver_number)
    except OpenF1HTTPError:
        # Some OpenF1 deployments ignore driver_number filter — retry session-wide.
        try:
            rows = await client.get_team_radio(session_key=session_key)
        except Exception:
            return []
    except Exception:
        return []

    cleaned: List[Dict[str, Any]] = []
    wanted = int(driver_number)
    for row in rows or []:
        number = row.get("driver_number")
        try:
            number_int = int(number) if number is not None else None
        except (TypeError, ValueError):
            number_int = None
        if number_int is not None and number_int != wanted:
            continue
        cleaned.append(
            {
                "date": row.get("date"),
                "driver_number": number_int if number_int is not None else wanted,
                "recording_url": row.get("recording_url"),
                "meeting_key": row.get("meeting_key"),
                "session_key": row.get("session_key"),
            }
        )
    return cleaned[:limit]


# Backwards-compatible aliases used by earlier drafts.
async def fetch_race_control(
    *,
    session_key: int,
    openf1: Optional[Any] = None,
    limit: int = 40,
    lap_number: Optional[int] = None,
) -> List[Dict[str, Any]]:
    return await get_race_control(session_key, lap_number, openf1=openf1, limit=limit)


async def fetch_team_radio(
    *,
    session_key: int,
    driver_numbers: Optional[List[int]] = None,
    openf1: Optional[Any] = None,
    limit: int = 30,
) -> List[Dict[str, Any]]:
    if not driver_numbers:
        # Session-wide radio pack (no driver filter).
        client = _client(openf1)
        try:
            rows = await client.get_team_radio(session_key=session_key)
        except Exception:
            return []
        cleaned = []
        for row in rows or []:
            cleaned.append(
                {
                    "date": row.get("date"),
                    "driver_number": row.get("driver_number"),
                    "recording_url": row.get("recording_url"),
                    "meeting_key": row.get("meeting_key"),
                    "session_key": row.get("session_key"),
                }
            )
        return cleaned[:limit]
    out: List[Dict[str, Any]] = []
    for number in driver_numbers:
        out.extend(await get_team_radio(session_key, int(number), openf1=openf1, limit=limit))
    return out[:limit]


def summarize_race_control(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return "Race control: no messages returned for this session window."
    lines = []
    for row in rows[:12]:
        stamp = row.get("date") or "?"
        cat = row.get("category") or "Message"
        flag = row.get("flag")
        msg = row.get("message") or ""
        flag_bit = " flag={0}".format(flag) if flag else ""
        lines.append("[{0}] {1}{2}: {3}".format(stamp, cat, flag_bit, msg))
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
