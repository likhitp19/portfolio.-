from __future__ import annotations

import base64
import json
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.agents.steward_graph import compiled_steward_graph, initial_steward_state
from app.schemas.steward import (
    LiveFeedContext,
    Phase2TelemetryIngestRequest,
    ProtestDossier,
    StewardAnalyzeRequest,
    StewardAnalyzeResponse,
    StewardVerdict,
)

router = APIRouter(prefix="/api/steward", tags=["steward"])

_MAX_INLINE_BYTES = 8_000_000
_DISCLAIMER = (
    "Simulated Team Principal Protest Dossier for a portfolio demo. "
    "Teaching-corpus rules only — not an official FIA Protest or Steward Decision."
)
_VERDICT_KEYS = ("incident", "rule_cited", "telemetry_facts", "verdict", "penalty")


def _response_from_state(state: Dict[str, Any]) -> StewardAnalyzeResponse:
    verdict = state.get("verdict") or {}
    dossier_raw = state.get("protest_dossier") or {}
    try:
        dossier = ProtestDossier.model_validate(dossier_raw)
    except Exception:
        dossier = ProtestDossier(
            primary_claim=str(verdict.get("incident") or ""),
            regulatory_violations=[
                {
                    "article_name": str(verdict.get("rule_cited") or "Unspecified citation"),
                    "exact_quote": str(verdict.get("rule_cited") or ""),
                    "page_number": 0,
                    "source_document": "teaching_corpus",
                }
            ]
            if verdict.get("rule_cited")
            else [],
            available_evidence_summary=str(verdict.get("telemetry_facts") or ""),
            success_probability="Low",
            legal_risk_notes="Dossier incomplete; Phase 2 evidence required.",
            recommended_next_step="Ingest Phase 2 micro-telemetry before lodging.",
        )
    return StewardAnalyzeResponse(
        vision=state.get("vision") or {},
        telemetry_summary=state.get("telemetry_summary") or "",
        telemetry_series=state.get("telemetry_series") or [],
        telemetry_degraded=bool(state.get("telemetry_degraded")),
        session_key=state.get("session_key_resolved"),
        retrieved_rules=state.get("retrieved_rules") or [],
        verdict=StewardVerdict(**{key: str(verdict.get(key) or "") for key in _VERDICT_KEYS}),
        protest_dossier=dossier,
        pipeline=state.get("pipeline") or [],
        assumptions=state.get("assumptions") or [],
        errors=state.get("errors") or [],
        disclaimer=_DISCLAIMER,
    )


def _ensure_input(
    clip_url: Optional[str],
    clip_data_url: Optional[str],
    incident_hint: str,
    live_feed: Optional[LiveFeedContext] = None,
) -> None:
    has_live = bool(
        live_feed
        and (
            live_feed.timing_note.strip()
            or live_feed.involved_driver_numbers
            or live_feed.lap_number is not None
        )
    )
    if clip_url or clip_data_url or (incident_hint or "").strip() or has_live:
        return
    raise HTTPException(
        status_code=422,
        detail={
            "code": "STEWARD_NO_INPUT",
            "message": "Provide a clip, incident_hint, or live_feed timing context.",
        },
    )


def _live_feed_dict(feed: Optional[LiveFeedContext]) -> Dict[str, Any]:
    if feed is None:
        return {}
    return feed.model_dump(exclude_none=True)


def _state_from_request(body: StewardAnalyzeRequest, *, clip_data_url: Optional[str] = None) -> Dict[str, Any]:
    return initial_steward_state(
        clip_url=body.clip_url,
        clip_data_url=clip_data_url,
        year=body.year,
        circuit=body.circuit,
        meeting_key=body.meeting_key,
        session_key=body.session_key,
        incident_hint=body.incident_hint,
        live_feed=_live_feed_dict(body.live_feed),
        filing_team=body.filing_team,
        filing_type=body.filing_type,
    )


def _data_url_from_upload(filename: str, payload: bytes) -> Optional[str]:
    if not payload or len(payload) > _MAX_INLINE_BYTES:
        return None
    suffix = (filename or "").lower()
    mime = "video/mp4"
    if suffix.endswith(".webm"):
        mime = "video/webm"
    elif suffix.endswith((".jpg", ".jpeg")):
        mime = "image/jpeg"
    elif suffix.endswith(".png"):
        mime = "image/png"
    encoded = base64.b64encode(payload).decode("ascii")
    return "data:{0};base64,{1}".format(mime, encoded)


@router.post("/analyze_clip", response_model=StewardAnalyzeResponse)
async def analyze_clip(body: StewardAnalyzeRequest) -> StewardAnalyzeResponse:
    _ensure_input(body.clip_url, None, body.incident_hint, body.live_feed)
    state = _state_from_request(body)
    result = await compiled_steward_graph.ainvoke(state)
    return _response_from_state(result)


@router.post("/analyze_clip/upload", response_model=StewardAnalyzeResponse)
async def analyze_clip_upload(
    file: UploadFile = File(...),
    year: Optional[int] = Form(None),
    circuit: Optional[str] = Form(None),
    meeting_key: Optional[int] = Form(None),
    session_key: Optional[int] = Form(None),
    incident_hint: str = Form(""),
    clip_url: Optional[str] = Form(None),
    live_feed_json: Optional[str] = Form(None),
    filing_team: str = Form("Mercedes-AMG Petronas Formula One Team"),
    filing_type: str = Form("protest"),
) -> StewardAnalyzeResponse:
    payload = await file.read()
    data_url = _data_url_from_upload(file.filename or "", payload)
    hint = incident_hint
    live_feed = None
    if live_feed_json:
        live_feed = LiveFeedContext.model_validate(json.loads(live_feed_json))
    if payload and data_url is None:
        hint = "{0} Uploaded clip exceeded inline vision size; using filename {1}.".format(
            hint, file.filename or "clip"
        ).strip()
    _ensure_input(clip_url, data_url, hint, live_feed)
    body = StewardAnalyzeRequest(
        clip_url=clip_url,
        year=year,
        circuit=circuit,
        meeting_key=meeting_key,
        session_key=session_key,
        incident_hint=hint,
        live_feed=live_feed,
        filing_team=filing_team,
        filing_type=filing_type if filing_type in {"protest", "right_of_review"} else "protest",
    )
    state = _state_from_request(body, clip_data_url=data_url)
    result = await compiled_steward_graph.ainvoke(state)
    return _response_from_state(result)


@router.post("/analyze_clip/stream")
async def analyze_clip_stream(body: StewardAnalyzeRequest) -> StreamingResponse:
    _ensure_input(body.clip_url, None, body.incident_hint, body.live_feed)
    state = _state_from_request(body)

    async def events_once() -> AsyncIterator[str]:
        seen = set()
        last: Dict[str, Any] = dict(state)
        async for update in compiled_steward_graph.astream(state, stream_mode="updates"):
            for _node, payload in (update or {}).items():
                if not isinstance(payload, dict):
                    continue
                last.update(payload)
                for item in payload.get("pipeline") or []:
                    stage = str(item.get("stage") or "")
                    if not stage or stage in seen:
                        continue
                    seen.add(stage)
                    yield "event: stage\ndata: {0}\n\n".format(json.dumps(item))
        yield "event: result\ndata: {0}\n\n".format(json.dumps(_response_from_state(last).model_dump()))

    return StreamingResponse(events_once(), media_type="text/event-stream")


@router.post("/phase2/telemetry")
async def phase2_telemetry_contract(body: Phase2TelemetryIngestRequest) -> Dict[str, Any]:
    """Phase 2 bridge (schema-only until high-frequency ingest is implemented)."""
    return {
        "accepted": False,
        "status": "PHASE2_NOT_IMPLEMENTED",
        "message": (
            "High-frequency telemetry ingest is specified but not yet implemented. "
            "Use this contract to prepare Phase 2 payloads that satisfy "
            "protest_dossier.required_telemetry_evidence."
        ),
        "received_channels": [channel.channel for channel in body.channels],
        "sample_hz_range": "10–100",
        "schema": Phase2TelemetryIngestRequest.model_json_schema(),
    }
