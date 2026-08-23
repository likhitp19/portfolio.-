from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.integrations.openf1 import OpenF1HTTPError


class JolpicaClient:
    """Ergast-compatible history for seasons OpenF1 does not list."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (base_url or settings.jolpica_base_url).rstrip("/")
        self._http = httpx.AsyncClient(timeout=20.0, headers={"Accept": "application/json"})

    async def aclose(self) -> None:
        await self._http.aclose()

    async def list_races(self, year: int) -> List[Dict[str, Any]]:
        url = "{0}/{1}/races.json".format(self.base_url, year)
        try:
            response = await self._http.get(url)
        except httpx.HTTPError as exc:
            raise OpenF1HTTPError(0, str(exc)) from exc
        if response.status_code == 404:
            return []
        if response.status_code >= 400:
            raise OpenF1HTTPError(response.status_code, response.text[:400])
        payload = response.json()
        races = (
            payload.get("MRData", {})
            .get("RaceTable", {})
            .get("Races", [])
        )
        meetings: List[Dict[str, Any]] = []
        for race in races:
            round_no = int(race.get("round") or 0)
            circuit = race.get("Circuit") or {}
            location = circuit.get("Location") or {}
            meetings.append(
                {
                    "meeting_key": year * 100 + round_no,
                    "year": year,
                    "meeting_name": str(race.get("raceName") or ""),
                    "circuit_short_name": str(circuit.get("circuitName") or circuit.get("circuitId") or ""),
                    "country_name": str(location.get("country") or ""),
                    "date_start": str(race.get("date") or "") or None,
                    "source": "jolpica",
                }
            )
        return meetings

    async def constructor_standings(self, year: int) -> List[Dict[str, Any]]:
        url = "{0}/{1}/constructorStandings.json".format(self.base_url, year)
        try:
            response = await self._http.get(url, params={"limit": 30})
        except httpx.HTTPError as exc:
            raise OpenF1HTTPError(0, str(exc)) from exc
        if response.status_code == 404:
            return []
        if response.status_code >= 400:
            raise OpenF1HTTPError(response.status_code, response.text[:400])
        payload = response.json()
        lists = (
            payload.get("MRData", {})
            .get("StandingsTable", {})
            .get("StandingsLists", [])
        )
        if not lists:
            return []
        rows: List[Dict[str, Any]] = []
        for item in lists[0].get("ConstructorStandings") or []:
            constructor = item.get("Constructor") or {}
            points = float(item.get("points") or 0)
            rows.append(
                {
                    "team_name": str(constructor.get("name") or constructor.get("constructorId") or ""),
                    "points": points,
                    "points_current": points,
                    "position": int(item.get("position") or 99),
                    "position_current": int(item.get("position") or 99),
                    "source": "jolpica",
                }
            )
        return rows

    async def driver_standings(self, year: int) -> List[Dict[str, Any]]:
        url = "{0}/{1}/driverStandings.json".format(self.base_url, year)
        try:
            response = await self._http.get(url, params={"limit": 40})
        except httpx.HTTPError as exc:
            raise OpenF1HTTPError(0, str(exc)) from exc
        if response.status_code == 404:
            return []
        if response.status_code >= 400:
            raise OpenF1HTTPError(response.status_code, response.text[:400])
        payload = response.json()
        lists = (
            payload.get("MRData", {})
            .get("StandingsTable", {})
            .get("StandingsLists", [])
        )
        if not lists:
            return []
        rows: List[Dict[str, Any]] = []
        for item in lists[0].get("DriverStandings") or []:
            driver = item.get("Driver") or {}
            points = float(item.get("points") or 0)
            number = driver.get("permanentNumber") or driver.get("code") or driver.get("driverId")
            given = str(driver.get("givenName") or "")
            family = str(driver.get("familyName") or "")
            rows.append(
                {
                    "driver_number": str(number or ""),
                    "full_name": ("{0} {1}".format(given, family)).strip() or str(driver.get("driverId") or ""),
                    "name_acronym": str(driver.get("code") or ""),
                    "points": points,
                    "points_current": points,
                    "position": int(item.get("position") or 99),
                    "position_current": int(item.get("position") or 99),
                    "source": "jolpica",
                }
            )
        return rows

    async def list_results(self, year: int) -> List[Dict[str, Any]]:
        url = "{0}/{1}/results.json".format(self.base_url, year)
        try:
            response = await self._http.get(url, params={"limit": 600})
        except httpx.HTTPError as exc:
            raise OpenF1HTTPError(0, str(exc)) from exc
        if response.status_code == 404:
            return []
        if response.status_code >= 400:
            raise OpenF1HTTPError(response.status_code, response.text[:400])
        payload = response.json()
        return (
            payload.get("MRData", {})
            .get("RaceTable", {})
            .get("Races", [])
        )
