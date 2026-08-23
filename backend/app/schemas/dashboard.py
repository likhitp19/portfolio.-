from typing import List, Optional

from pydantic import BaseModel, Field


class SeasonsResponse(BaseModel):
    years: List[int] = Field(default_factory=list)


class Meeting(BaseModel):
    meeting_key: int
    year: int
    meeting_name: str
    circuit_short_name: str
    country_name: str
    date_start: Optional[str] = None


class FactCitation(BaseModel):
    status: str = "estimate"
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    retrieved_at: Optional[str] = None
    value_low: Optional[float] = None
    value_high: Optional[float] = None
    snippet: Optional[str] = None


class DriverStanding(BaseModel):
    driver_number: int
    full_name: str
    team_name: str
    points: float
    position: int
    salary_usd: Optional[float] = None
    financial_efficiency: Optional[float] = None
    salary: Optional[FactCitation] = None


class ConstructorStanding(BaseModel):
    team_name: str
    points: float
    position: int
    valuation_usd: Optional[float] = None
    budget_cap_usd: Optional[float] = None
    cost_per_point: Optional[float] = None
    wins: int = 0
    avg_wins: float = 0.0
    valuation: Optional[FactCitation] = None
    budget_cap: Optional[FactCitation] = None


class Top3FinishCount(BaseModel):
    driver_name: str
    count: int


class ChampionshipSummary(BaseModel):
    leader_name: Optional[str] = None
    leader_points: Optional[float] = None
    points_gap: Optional[float] = None
    race_count: int = 0
    fastest_lap_driver: Optional[str] = None
    fastest_lap_duration: Optional[float] = None
    total_dnfs: int = 0
    top3_finishes: List[Top3FinishCount] = Field(default_factory=list)
    best_manufacturer: Optional[str] = None
    best_manufacturer_reason: Optional[str] = None


class CircuitLabel(BaseModel):
    meeting_key: int
    name: str


class ProgressionSeries(BaseModel):
    driver: str
    points: List[float] = Field(default_factory=list)


class StandingsProgression(BaseModel):
    circuits: List[CircuitLabel] = Field(default_factory=list)
    series: List[ProgressionSeries] = Field(default_factory=list)


class DashboardOverview(BaseModel):
    year: int
    meeting_key: Optional[int] = None
    years: List[int] = Field(default_factory=list)
    meetings: List[Meeting] = Field(default_factory=list)
    drivers: List[DriverStanding] = Field(default_factory=list)
    constructors: List[ConstructorStanding] = Field(default_factory=list)
    summary: ChampionshipSummary = Field(default_factory=ChampionshipSummary)
    progression: StandingsProgression = Field(default_factory=StandingsProgression)
    constructor_progression: StandingsProgression = Field(default_factory=StandingsProgression)
