from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.integrations.openf1 import OpenF1Client
from app.runtime import get_client, get_fact_store, get_search_client
from app.schemas.dashboard import (
    ChampionshipSummary,
    ConstructorStanding,
    DashboardOverview,
    DriverStanding,
    Meeting,
    SeasonsResponse,
    StandingsProgression,
)
from app.services import dashboard as svc
from app.services.commercial import refresh_commercial_facts

router = APIRouter(prefix="/api")


def openf1_dep() -> OpenF1Client:
    return get_client()


@router.get("/seasons", response_model=SeasonsResponse)
async def get_seasons(client: OpenF1Client = Depends(openf1_dep)) -> SeasonsResponse:
    return await svc.list_seasons(client)


@router.get("/meetings", response_model=List[Meeting])
async def get_meetings(
    year: int = Query(...),
    client: OpenF1Client = Depends(openf1_dep),
) -> List[Meeting]:
    return await svc.list_meetings(client, year)


@router.get("/championship/drivers", response_model=List[DriverStanding])
async def get_championship_drivers(
    year: int = Query(...),
    meeting_key: Optional[int] = None,
    session_key: Optional[int] = None,
    client: OpenF1Client = Depends(openf1_dep),
) -> List[DriverStanding]:
    return await svc.driver_standings(client, year, meeting_key, session_key)


@router.get("/championship/constructors", response_model=List[ConstructorStanding])
async def get_championship_constructors(
    year: int = Query(...),
    meeting_key: Optional[int] = None,
    session_key: Optional[int] = None,
    client: OpenF1Client = Depends(openf1_dep),
) -> List[ConstructorStanding]:
    return await svc.constructor_standings(client, year, meeting_key, session_key)


@router.get("/championship/summary", response_model=ChampionshipSummary)
async def get_championship_summary(
    year: int = Query(...),
    meeting_key: Optional[int] = None,
    client: OpenF1Client = Depends(openf1_dep),
) -> ChampionshipSummary:
    return await svc.championship_summary(client, year, meeting_key)


@router.get("/standings/progression", response_model=StandingsProgression)
async def get_standings_progression(
    year: int = Query(...),
    client: OpenF1Client = Depends(openf1_dep),
) -> StandingsProgression:
    return await svc.standings_progression(client, year)


@router.get("/dashboard", response_model=DashboardOverview)
async def get_dashboard(
    year: int = Query(...),
    meeting_key: Optional[int] = None,
    client: OpenF1Client = Depends(openf1_dep),
) -> DashboardOverview:
    return await svc.dashboard_overview(client, year, meeting_key)


@router.get("/facts/commercial")
async def get_commercial_facts(year: int = Query(...)) -> Dict[str, Any]:
    store = get_fact_store()
    return {"year": year, "facts": store.list_year(year)}


class FactsRefreshBody(BaseModel):
    year: int
    force: bool = False
    team_names: Optional[List[str]] = None


@router.post("/facts/refresh")
async def post_facts_refresh(
    body: FactsRefreshBody,
    client: OpenF1Client = Depends(openf1_dep),
) -> Dict[str, Any]:
    teams = body.team_names
    if not teams:
        constructors = await svc.constructor_standings(client, body.year)
        teams = [row.team_name for row in constructors]
    return await refresh_commercial_facts(
        get_fact_store(),
        get_search_client(),
        body.year,
        teams,
        force=body.force,
    )
