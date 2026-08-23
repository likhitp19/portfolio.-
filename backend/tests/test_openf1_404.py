import asyncio

import httpx

from app.integrations.openf1 import OpenF1Client


def test_openf1_404_is_empty_list() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "No results found."})

    async def _run() -> None:
        client = OpenF1Client(min_interval_seconds=0)
        await client.aclose()
        client._http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        rows = await client.get_championship_drivers(session_key=999)
        assert rows == []
        await client.aclose()

    asyncio.run(_run())


def test_openf1_401_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "Live F1 session in progress."})

    async def _run() -> None:
        from app.integrations.openf1 import OpenF1HTTPError

        client = OpenF1Client(min_interval_seconds=0)
        await client.aclose()
        client._http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            await client.list_meetings(year=2025)
            raise AssertionError("expected 401")
        except OpenF1HTTPError as exc:
            assert exc.status_code == 401
        await client.aclose()

    asyncio.run(_run())


def test_live_session_maps_to_503() -> None:
    from app.integrations.openf1 import OpenF1HTTPError
    from app.services.dashboard import _http_or_502

    err = _http_or_502(OpenF1HTTPError(401, "live lock"))
    assert err.status_code == 503
    assert err.detail["code"] == "F1_LIVE_LOCK"
    assert "on air" in err.detail["message"].lower() or "session" in err.detail["message"].lower()
