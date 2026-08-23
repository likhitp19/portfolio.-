from typing import Any, Dict, List, Optional

from app.integrations.openf1 import OpenF1HTTPError


class FakeOpenF1Client:
    def __init__(self, fail_resource: Optional[str] = None, fail_status: int = 500) -> None:
        self.fail_resource = fail_resource
        self.fail_status = fail_status
        self.calls: List[Dict[str, Any]] = []
        self.meetings: List[Dict[str, Any]] = [
            {
                "meeting_key": 1,
                "year": 2024,
                "meeting_name": "Bahrain Grand Prix",
                "circuit_short_name": "Sakhir",
                "country_name": "Bahrain",
                "date_start": "2024-03-02T00:00:00+00:00",
            },
            {
                "meeting_key": 2,
                "year": 2024,
                "meeting_name": "Saudi Arabian Grand Prix",
                "circuit_short_name": "Jeddah",
                "country_name": "Saudi Arabia",
                "date_start": "2024-03-09T00:00:00+00:00",
            },
        ]
        self.sessions: List[Dict[str, Any]] = [
            {
                "session_key": 101,
                "meeting_key": 1,
                "year": 2024,
                "session_name": "Race",
                "session_type": "Race",
                "date_start": "2024-03-02T15:00:00+00:00",
                "date_end": "2024-03-02T17:00:00+00:00",
                "circuit_short_name": "Sakhir",
            },
            {
                "session_key": 201,
                "meeting_key": 2,
                "year": 2024,
                "session_name": "Race",
                "session_type": "Race",
                "date_start": "2024-03-09T18:00:00+00:00",
                "date_end": "2024-03-09T20:00:00+00:00",
                "circuit_short_name": "Jeddah",
            },
        ]
        self.drivers = [
            {"session_key": 201, "driver_number": 1, "full_name": "Max Verstappen", "team_name": "Red Bull Racing"},
            {"session_key": 201, "driver_number": 11, "full_name": "Sergio Perez", "team_name": "Red Bull Racing"},
            {"session_key": 201, "driver_number": 4, "full_name": "Lando Norris", "team_name": "McLaren"},
            {"session_key": 201, "driver_number": 81, "full_name": "Oscar Piastri", "team_name": "McLaren"},
            {"session_key": 201, "driver_number": 16, "full_name": "Charles Leclerc", "team_name": "Ferrari"},
            {"session_key": 201, "driver_number": 44, "full_name": "Lewis Hamilton", "team_name": "Mercedes"},
        ]
        self.championship_by_session = {
            101: [
                {"driver_number": 1, "full_name": "Max Verstappen", "team_name": "Red Bull Racing", "points_current": 25, "position_current": 1},
                {"driver_number": 4, "full_name": "Lando Norris", "team_name": "McLaren", "points_current": 18, "position_current": 2},
                {"driver_number": 16, "full_name": "Charles Leclerc", "team_name": "Ferrari", "points_current": 15, "position_current": 3},
                {"driver_number": 81, "full_name": "Oscar Piastri", "team_name": "McLaren", "points_current": 12, "position_current": 4},
                {"driver_number": 44, "full_name": "Lewis Hamilton", "team_name": "Mercedes", "points_current": 10, "position_current": 5},
                {"driver_number": 11, "full_name": "Sergio Perez", "team_name": "Red Bull Racing", "points_current": 8, "position_current": 6},
            ],
            201: [
                {"driver_number": 1, "full_name": "Max Verstappen", "team_name": "Red Bull Racing", "points_current": 43, "position_current": 1},
                {"driver_number": 4, "full_name": "Lando Norris", "team_name": "McLaren", "points_current": 36, "position_current": 2},
                {"driver_number": 81, "full_name": "Oscar Piastri", "team_name": "McLaren", "points_current": 30, "position_current": 3},
                {"driver_number": 16, "full_name": "Charles Leclerc", "team_name": "Ferrari", "points_current": 28, "position_current": 4},
                {"driver_number": 44, "full_name": "Lewis Hamilton", "team_name": "Mercedes", "points_current": 20, "position_current": 5},
                {"driver_number": 11, "full_name": "Sergio Perez", "team_name": "Red Bull Racing", "points_current": 18, "position_current": 6},
            ],
        }
        self.teams_by_session = {
            101: [
                {"team_name": "Red Bull Racing", "points_current": 33, "position_current": 1},
                {"team_name": "McLaren", "points_current": 30, "position_current": 2},
                {"team_name": "Ferrari", "points_current": 15, "position_current": 3},
                {"team_name": "Mercedes", "points_current": 10, "position_current": 4},
            ],
            201: [
                {"team_name": "McLaren", "points_current": 66, "position_current": 1},
                {"team_name": "Red Bull Racing", "points_current": 61, "position_current": 2},
                {"team_name": "Ferrari", "points_current": 28, "position_current": 3},
                {"team_name": "Mercedes", "points_current": 20, "position_current": 4},
            ],
        }
        self.race_control = [
            {
                "meeting_key": 1,
                "session_key": 101,
                "date": "2024-03-02T15:10:00+00:00",
                "category": "Flag",
                "message": "YELLOW IN ZONE 2",
            }
        ]
        self.laps = [
            {"session_key": 101, "driver_number": 1, "lap_number": 10, "lap_duration": 93.4},
            {"session_key": 201, "driver_number": 4, "lap_number": 12, "lap_duration": 91.2},
        ]
        self.session_results = [
            {"session_key": 101, "driver_number": 1, "position": 1, "dnf": False, "team_name": "Red Bull Racing"},
            {"session_key": 101, "driver_number": 4, "position": 2, "dnf": False, "team_name": "McLaren"},
            {"session_key": 101, "driver_number": 16, "position": 3, "dnf": False, "team_name": "Ferrari"},
            {"session_key": 101, "driver_number": 11, "position": 99, "dnf": True, "team_name": "Red Bull Racing"},
            {"session_key": 201, "driver_number": 1, "position": 1, "dnf": False, "team_name": "Red Bull Racing"},
            {"session_key": 201, "driver_number": 4, "position": 2, "dnf": False, "team_name": "McLaren"},
            {"session_key": 201, "driver_number": 81, "position": 3, "dnf": False, "team_name": "McLaren"},
            {"session_key": 201, "driver_number": 44, "position": 99, "dnf": True, "team_name": "Mercedes"},
        ]

    def _record(self, tool: str, **params: Any) -> None:
        self.calls.append({"tool": tool, "params": params})
        if self.fail_resource == tool:
            status = self.fail_status or 500
            text = "Live F1 session in progress." if status == 401 else "forced failure"
            raise OpenF1HTTPError(status, text)

    def _filter(self, rows: List[Dict[str, Any]], **params: Any) -> List[Dict[str, Any]]:
        out = rows
        for key, value in params.items():
            if value is None:
                continue
            out = [row for row in out if row.get(key) == value or str(row.get(key)) == str(value)]
        return out

    async def list_meetings(self, **params: Any) -> List[Dict[str, Any]]:
        self._record("list_meetings", **params)
        return self._filter(self.meetings, **params)

    async def list_sessions(self, **params: Any) -> List[Dict[str, Any]]:
        self._record("list_sessions", **params)
        return self._filter(self.sessions, **params)

    async def get_drivers(self, **params: Any) -> List[Dict[str, Any]]:
        self._record("get_drivers", **params)
        return self._filter(self.drivers, **params)

    async def get_championship_drivers(self, **params: Any) -> List[Dict[str, Any]]:
        self._record("get_championship_drivers", **params)
        session_key = params.get("session_key")
        if session_key is not None:
            return list(self.championship_by_session.get(int(session_key), []))
        if params.get("year") is not None:
            rows: List[Dict[str, Any]] = []
            for key, items in self.championship_by_session.items():
                for item in items:
                    row = dict(item)
                    row["session_key"] = key
                    row["year"] = int(params["year"])
                    rows.append(row)
            return rows
        return []

    async def get_championship_teams(self, **params: Any) -> List[Dict[str, Any]]:
        self._record("get_championship_teams", **params)
        session_key = params.get("session_key")
        if session_key is not None:
            return list(self.teams_by_session.get(int(session_key), []))
        if params.get("year") is not None:
            latest = max(self.teams_by_session.keys())
            return list(self.teams_by_session.get(latest, []))
        return []

    async def get_session_result(self, **params: Any) -> List[Dict[str, Any]]:
        self._record("get_session_result", **params)
        return self._filter(self.session_results, **params)

    async def get_laps(self, **params: Any) -> List[Dict[str, Any]]:
        self._record("get_laps", **params)
        return self._filter(self.laps, **params)

    async def get_position(self, **params: Any) -> List[Dict[str, Any]]:
        self._record("get_position", **params)
        return []

    async def get_stints(self, **params: Any) -> List[Dict[str, Any]]:
        self._record("get_stints", **params)
        return []

    async def get_race_control(self, **params: Any) -> List[Dict[str, Any]]:
        self._record("get_race_control", **params)
        return self._filter(self.race_control, **params)

    async def get_weather(self, **params: Any) -> List[Dict[str, Any]]:
        self._record("get_weather", **params)
        return []

    async def aclose(self) -> None:
        return None
