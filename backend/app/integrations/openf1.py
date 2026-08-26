import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx

from app.config import settings


class OpenF1HTTPError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__("OpenF1 HTTP {0}: {1}".format(status_code, message))


class OpenF1Client:
    """OpenF1 client with TTL cache, throttle, and optional OAuth during live sessions."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        ttl_seconds: int = 300,
        min_interval_seconds: float = 0.35,
    ) -> None:
        self.base_url = (base_url or settings.openf1_base_url).rstrip("/")
        self.ttl_seconds = ttl_seconds
        self.min_interval_seconds = min_interval_seconds
        headers = {"Accept": "application/json"}
        static = (settings.openf1_access_token or "").strip()
        if static:
            headers["Authorization"] = "Bearer {0}".format(static)
        self._http = httpx.AsyncClient(timeout=30.0, headers=headers)
        self._cache: Dict[Tuple[Any, ...], Tuple[float, List[Dict[str, Any]]]] = {}
        self._lock: Optional[asyncio.Lock] = None
        self._next_slot = 0.0
        self._token: Optional[str] = static or None
        self._token_expires_at = 0.0 if not static else time.time() + 3600

    def _auth_origin(self) -> str:
        parsed = urlparse(self.base_url if "://" in self.base_url else "https://" + self.base_url)
        if parsed.scheme and parsed.netloc:
            return "{0}://{1}".format(parsed.scheme, parsed.netloc)
        return "https://api.openf1.org"

    async def aclose(self) -> None:
        await self._http.aclose()

    def _cache_key(self, resource: str, params: Dict[str, Any]) -> Tuple[Any, ...]:
        items = tuple(sorted((k, str(v)) for k, v in params.items()))
        return (resource, items)

    async def _throttle(self) -> None:
        if self._lock is None:
            self._lock = asyncio.Lock()
        async with self._lock:
            now = time.monotonic()
            wait = self._next_slot - now
            if wait > 0:
                await asyncio.sleep(wait)
            self._next_slot = time.monotonic() + self.min_interval_seconds

    async def _ensure_token(self) -> None:
        username = (settings.openf1_username or "").strip()
        password = (settings.openf1_password or "").strip()
        if not username or not password:
            return
        if self._token and time.time() < self._token_expires_at - 60:
            self._http.headers["Authorization"] = "Bearer {0}".format(self._token)
            return
        token_url = "{0}/token".format(self._auth_origin())
        self._http.headers.pop("Authorization", None)
        response = await self._http.post(
            token_url,
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        )
        if response.status_code >= 400:
            raise OpenF1HTTPError(response.status_code, "Token request failed: {0}".format(response.text[:400]))
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise OpenF1HTTPError(401, "OpenF1 token response missing access_token")
        expires = float(payload.get("expires_in") or 3600)
        self._token = token
        self._token_expires_at = time.time() + expires
        self._http.headers["Authorization"] = "Bearer {0}".format(token)

    async def _get(self, resource: str, **params: Any) -> List[Dict[str, Any]]:
        clean = {k: v for k, v in params.items() if v is not None}
        if str(clean.get("session_key", "")).lower() == "latest":
            return []
        key = self._cache_key(resource, clean)
        hit = self._cache.get(key)
        if hit and (time.time() - hit[0]) < self.ttl_seconds:
            return hit[1]

        last_error = None
        for attempt in range(4):
            await self._throttle()
            await self._ensure_token()
            try:
                response = await self._http.get("{0}/{1}".format(self.base_url, resource), params=clean)
                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After") or 1.0)
                    await asyncio.sleep(max(retry_after, 1.0))
                    last_error = OpenF1HTTPError(429, response.text[:500])
                    continue
                if response.status_code == 401:
                    self._token = None
                    self._token_expires_at = 0.0
                    if attempt < 2 and (settings.openf1_username or "").strip():
                        continue
                    raise OpenF1HTTPError(401, response.text[:500])
                if response.status_code == 404:
                    self._cache[key] = (time.time(), [])
                    return []
                response.raise_for_status()
            except OpenF1HTTPError:
                raise
            except httpx.HTTPStatusError as exc:
                body = exc.response.text[:500]
                raise OpenF1HTTPError(exc.response.status_code, body) from exc
            except httpx.HTTPError as exc:
                raise OpenF1HTTPError(0, str(exc)) from exc

            payload = response.json()
            if payload is None:
                data = []
            elif isinstance(payload, list):
                data = payload
            else:
                data = [payload]
            self._cache[key] = (time.time(), data)
            return data

        raise last_error or OpenF1HTTPError(429, "Rate limit exceeded")

    async def list_meetings(self, **params: Any) -> List[Dict[str, Any]]:
        return await self._get("meetings", **params)

    async def list_sessions(self, **params: Any) -> List[Dict[str, Any]]:
        return await self._get("sessions", **params)

    async def get_drivers(self, **params: Any) -> List[Dict[str, Any]]:
        return await self._get("drivers", **params)

    async def get_championship_drivers(self, **params: Any) -> List[Dict[str, Any]]:
        return await self._get("championship_drivers", **params)

    async def get_championship_teams(self, **params: Any) -> List[Dict[str, Any]]:
        return await self._get("championship_teams", **params)

    async def get_session_result(self, **params: Any) -> List[Dict[str, Any]]:
        return await self._get("session_result", **params)

    async def get_laps(self, **params: Any) -> List[Dict[str, Any]]:
        return await self._get("laps", **params)

    async def get_position(self, **params: Any) -> List[Dict[str, Any]]:
        return await self._get("position", **params)

    async def get_stints(self, **params: Any) -> List[Dict[str, Any]]:
        return await self._get("stints", **params)

    async def get_race_control(self, **params: Any) -> List[Dict[str, Any]]:
        return await self._get("race_control", **params)

    async def get_weather(self, **params: Any) -> List[Dict[str, Any]]:
        return await self._get("weather", **params)

    async def get_car_data(self, **params: Any) -> List[Dict[str, Any]]:
        return await self._get("car_data", **params)

    async def get_location(self, **params: Any) -> List[Dict[str, Any]]:
        return await self._get("location", **params)

    async def get_team_radio(self, **params: Any) -> List[Dict[str, Any]]:
        return await self._get("team_radio", **params)
