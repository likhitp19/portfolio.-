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
            constructor_id = str(constructor.get("constructorId") or "")
            rows.append(
                {
                    "team_name": str(constructor.get("name") or constructor_id),
                    "constructor_id": constructor_id,
                    "points": points,
                    "points_current": points,
                    "position": int(item.get("position") or 99),
                    "position_current": int(item.get("position") or 99),
                    "wins": int(item.get("wins") or 0),
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
            constructors = item.get("Constructors") or []
            constructor = constructors[0] if constructors else {}
            constructor_id = str(constructor.get("constructorId") or "")
            rows.append(
                {
                    "driver_number": str(number or ""),
                    "full_name": ("{0} {1}".format(given, family)).strip() or str(driver.get("driverId") or ""),
                    "name_acronym": str(driver.get("code") or ""),
                    "team_name": str(constructor.get("name") or constructor_id),
                    "constructor_id": constructor_id,
                    "points": points,
                    "points_current": points,
                    "position": int(item.get("position") or 99),
                    "position_current": int(item.get("position") or 99),
                    "source": "jolpica",
                }
            )
        return rows

    async def list_results(self, year: int) -> List[Dict[str, Any]]:
        """Paginate Ergast/Jolpica results. A single page is ~30 rows (one GP), not a season."""
        url = "{0}/{1}/results.json".format(self.base_url, year)
        by_round: Dict[str, Dict[str, Any]] = {}
        offset = 0
        page_size = 100
        total = None
        while True:
            try:
                response = await self._http.get(url, params={"limit": page_size, "offset": offset})
            except httpx.HTTPError as exc:
                raise OpenF1HTTPError(0, str(exc)) from exc
            if response.status_code == 404:
                break
            if response.status_code >= 400:
                raise OpenF1HTTPError(response.status_code, response.text[:400])
            payload = response.json()
            mr = payload.get("MRData") or {}
            total = int(mr.get("total") or 0)
            batch = (mr.get("RaceTable") or {}).get("Races") or []
            if not batch:
                break
            merge_ergast_race_pages(by_round, batch)
            fetched = int(mr.get("limit") or page_size)
            offset += fetched
            if total and offset >= total:
                break
            if not total and len(batch) < page_size:
                break
        return [
            by_round[key]
            for key in sorted(by_round, key=lambda item: int(item) if str(item).isdigit() else 0)
        ]

    async def list_qualifying(self, year: int) -> List[Dict[str, Any]]:
        """Paginate Ergast/Jolpica qualifying. One page is not a full season."""
        url = "{0}/{1}/qualifying.json".format(self.base_url, year)
        by_round: Dict[str, Dict[str, Any]] = {}
        offset = 0
        page_size = 100
        total = None
        while True:
            try:
                response = await self._http.get(url, params={"limit": page_size, "offset": offset})
            except httpx.HTTPError as exc:
                raise OpenF1HTTPError(0, str(exc)) from exc
            if response.status_code == 404:
                break
            if response.status_code >= 400:
                raise OpenF1HTTPError(response.status_code, response.text[:400])
            payload = response.json()
            mr = payload.get("MRData") or {}
            total = int(mr.get("total") or 0)
            batch = (mr.get("RaceTable") or {}).get("Races") or []
            if not batch:
                break
            merge_ergast_quali_pages(by_round, batch)
            fetched = int(mr.get("limit") or page_size)
            offset += fetched
            if total and offset >= total:
                break
            if not total and len(batch) < page_size:
                break
        return [
            by_round[key]
            for key in sorted(by_round, key=lambda item: int(item) if str(item).isdigit() else 0)
        ]


def merge_ergast_quali_pages(by_round: Dict[str, Dict[str, Any]], batch: List[Dict[str, Any]]) -> None:
    for race in batch:
        key = str(race.get("round") or race.get("raceName") or "")
        if not key:
            continue
        existing = by_round.get(key)
        if existing is None:
            copied = dict(race)
            copied["QualifyingResults"] = list(race.get("QualifyingResults") or [])
            by_round[key] = copied
        else:
            existing.setdefault("QualifyingResults", []).extend(race.get("QualifyingResults") or [])


def merge_ergast_race_pages(by_round: Dict[str, Dict[str, Any]], batch: List[Dict[str, Any]]) -> None:
    for race in batch:
        key = str(race.get("round") or race.get("raceName") or "")
        if not key:
            continue
        existing = by_round.get(key)
        if existing is None:
            copied = dict(race)
            copied["Results"] = list(race.get("Results") or [])
            by_round[key] = copied
        else:
            existing.setdefault("Results", []).extend(race.get("Results") or [])
