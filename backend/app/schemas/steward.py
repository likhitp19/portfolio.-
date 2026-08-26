from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class LiveFeedContext(BaseModel):
    """Timing / broadcast overlay facts available during a live session.

    This is NOT the steward verdict — only session context a real pitwall would
    already know (lap counter, car numbers, corner call from timing).
    """

    session_type: Optional[str] = None
    lap_number: Optional[int] = None
    involved_driver_numbers: List[int] = Field(default_factory=list)
    timing_note: str = ""

    @field_validator("involved_driver_numbers", mode="before")
    @classmethod
    def _coerce_driver_numbers(cls, value: Any) -> List[int]:
        if value is None:
            return []
        if not isinstance(value, list):
            return []
        out: List[int] = []
        for item in value:
            try:
                number = int(item)
            except (TypeError, ValueError):
                continue
            if 1 <= number <= 99:
                out.append(number)
        return list(dict.fromkeys(out))


class StewardAnalyzeRequest(BaseModel):
    clip_url: Optional[str] = None
    year: Optional[int] = None
    circuit: Optional[str] = None
    meeting_key: Optional[int] = None
    session_key: Optional[int] = None
    incident_hint: str = ""
    live_feed: Optional[LiveFeedContext] = None
    filing_team: str = "Mercedes-AMG Petronas Formula One Team"
    filing_type: Literal["protest", "right_of_review"] = "protest"


class StewardVerdict(BaseModel):
    """Legacy summary fields retained for compatibility with earlier steward UI."""

    incident: str = ""
    rule_cited: str = ""
    telemetry_facts: str = ""
    verdict: str = ""
    penalty: str = ""


EvidenceStatus = Literal["present", "pending_phase2", "insufficient"]
SuccessProbability = Literal["Low", "Medium", "High"]


class RequiredEvidenceItem(BaseModel):
    id: str = ""
    label: str = ""
    rationale: str = ""
    status: EvidenceStatus = "pending_phase2"
    phase2_schema_ref: str = ""


class RegulatoryCitation(BaseModel):
    """Verbatim regulation cite — quote must not be paraphrased by counsel."""

    article_name: str = ""
    exact_quote: str = ""
    page_number: int = 0
    source_document: str = ""

    @field_validator("page_number", mode="before")
    @classmethod
    def _coerce_page(cls, value: Any) -> int:
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0


class ProtestDossier(BaseModel):
    """Phase 1 output: Team Principal Protest / Right of Review dossier."""

    filing_type: Literal["protest", "right_of_review"] = "protest"
    filing_team: str = "Mercedes-AMG Petronas Formula One Team"
    competitor_team: str = ""
    primary_claim: str = ""
    regulatory_violations: List[RegulatoryCitation] = Field(default_factory=list)
    available_evidence_summary: str = ""
    required_telemetry_evidence: List[RequiredEvidenceItem] = Field(default_factory=list)
    success_probability: SuccessProbability = "Low"
    legal_risk_notes: str = ""
    recommended_next_step: str = ""
    phase2_bridge: str = (
        "Ingest high-frequency micro-telemetry via POST /api/steward/phase2/telemetry "
        "to satisfy pending evidentiary items before lodging with the FIA."
    )

    @field_validator("regulatory_violations", mode="before")
    @classmethod
    def _coerce_violations(cls, value: Any) -> List[Any]:
        if value is None:
            return []
        if not isinstance(value, list):
            return []
        out: List[Any] = []
        for item in value:
            if isinstance(item, dict):
                out.append(item)
            elif isinstance(item, str) and item.strip():
                out.append(
                    {
                        "article_name": item.strip()[:120],
                        "exact_quote": item.strip(),
                        "page_number": 0,
                        "source_document": "teaching_corpus",
                    }
                )
        return out


class Phase2TelemetryChannel(BaseModel):
    """Future Phase 2 contract: one high-frequency channel for a driver."""

    driver_number: int
    channel: Literal[
        "steering_angle_deg",
        "brake_pressure_bar",
        "throttle_pct",
        "speed_kph",
        "lateral_g",
        "longitudinal_g",
        "gps_x",
        "gps_y",
    ]
    sample_hz: float = Field(ge=10, le=100, description="10Hz–100Hz micro-telemetry")
    timestamps_iso: List[str] = Field(default_factory=list)
    values: List[float] = Field(default_factory=list)
    window_label: str = ""  # e.g. "Turn 5: 100m board → apex"


class Phase2TelemetryIngestRequest(BaseModel):
    """API contract for Phase 2 high-frequency telemetry ingestion (future scope)."""

    protest_ref: str = ""
    session_key: Optional[int] = None
    lap_number: Optional[int] = None
    turn_label: str = ""
    channels: List[Phase2TelemetryChannel] = Field(default_factory=list)
    onboard_tcam_url: Optional[str] = None
    notes: str = ""


class StewardAnalyzeResponse(BaseModel):
    vision: Dict[str, Any] = Field(default_factory=dict)
    telemetry_summary: str = ""
    telemetry_series: List[Dict[str, Any]] = Field(default_factory=list)
    telemetry_degraded: bool = False
    session_key: Optional[int] = None
    retrieved_rules: List[Dict[str, Any]] = Field(default_factory=list)
    verdict: StewardVerdict = Field(default_factory=StewardVerdict)
    protest_dossier: ProtestDossier = Field(default_factory=ProtestDossier)
    pipeline: List[Dict[str, Any]] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    disclaimer: str = (
        "Simulated Team Principal Protest Dossier for a portfolio demo. "
        "Teaching-corpus rules only — not an official FIA Protest or Steward Decision."
    )
