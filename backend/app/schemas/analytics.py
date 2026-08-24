from typing import List, Optional

from pydantic import BaseModel, Field


class RegulatoryEra(BaseModel):
    id: str
    label: str
    start_year: int
    end_year: int


class ConstructorTimelineSeries(BaseModel):
    constructor_id: str
    display_name: str
    points: List[Optional[float]] = Field(default_factory=list)
    positions: List[Optional[int]] = Field(default_factory=list)


class ConstructorTimeline(BaseModel):
    from_year: int
    to_year: int
    years: List[int] = Field(default_factory=list)
    series: List[ConstructorTimelineSeries] = Field(default_factory=list)
    eras: List[RegulatoryEra] = Field(default_factory=list)
    source: str = "jolpica"


class TeammateDeltaRow(BaseModel):
    constructor_id: str
    team_name: str
    driver_a_name: str
    driver_b_name: str
    points_a: float
    points_b: float
    points_share_pct: float
    dominant_share_pct: float
    quali_pace_delta_ms: Optional[float] = None
    signed_delta_ms: Optional[float] = None
    sample_races: int = 0
    quadrant: str = "watch"


class TeammateDeltaMatrix(BaseModel):
    year: int
    rows: List[TeammateDeltaRow] = Field(default_factory=list)
    share_risk_pct: float = 62.0
    quali_risk_ms: float = 200.0
    source: str = "jolpica"
