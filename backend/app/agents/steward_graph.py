from __future__ import annotations

import base64
import json
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, TypedDict
from urllib.parse import urlparse

import httpx
from langgraph.graph import END, START, StateGraph

from app.config import settings
from app.integrations.openf1 import OpenF1HTTPError
from app.services.rag_service import retrieve_rules as default_retrieve_rules

VisionFn = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
ReasonFn = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
RetrieveFn = Callable[[str, int], List[Dict[str, Any]]]

EMPTY_VERDICT = {
    "incident": "",
    "rule_cited": "",
    "telemetry_facts": "",
    "verdict": "",
    "penalty": "",
}

VISION_PROMPT = """You are a Formula 1 broadcast analyst. Inspect still frames from an incident clip
(onboard / world feed). Read on-screen TV graphics and telemetry overlays carefully.

Return ONLY JSON with this exact shape:
{{
  "circuit": "Identified circuit name or Unknown",
  "session_type": "Race|Qualifying|Sprint|Practice|Unknown",
  "lap_number": 0,
  "involved_driver_numbers": [0],
  "spatial_description": "one paragraph: positioning, apex lines, contact, racing room, braking / turn-in"
}}

Rules:
- Prefer circuit / lap / car numbers visible on timing bugs, overlays, or cars.
- Driver numbers must be integers from cars, timing overlays, or clearly readable race numbers.
- If a field is unknown, use null for lap_number, [] for numbers, "Unknown" for circuit/session_type,
  and still write spatial_description from what is visible.
- Do not decide a penalty. Do not invent championship context.
Optional metadata from the operator: year={year}, circuit={circuit}, hint={hint}
"""

REASON_PROMPT = """You are legal counsel for a Formula 1 Team Principal preparing an FIA Protest
or Article 14 Right of Review briefing for a software portfolio demo.
You are NOT lodging a real Protest and you are NOT issuing a Steward Decision.

Filing team: {filing_team}
Filing type: {filing_type}

Vision extract:
{vision}

OpenF1 telemetry summary (may be coarse / degraded):
{telemetry}

FIA regulation chunks (use EXACT wording from these chunks — do not paraphrase):
{rules}

Write JSON only with this exact shape:
{{
  "primary_claim": "formal allegation the Team Principal would assert",
  "competitor_team": "opposing competitor if inferable, else empty string",
  "regulatory_violations": [
    {{
      "article_name": "Article / Appendix title from the chunk",
      "exact_quote": "VERBATIM quote copied from the RAG chunk text — do not paraphrase",
      "page_number": 0,
      "source_document": "source_document from chunk metadata"
    }}
  ],
  "available_evidence_summary": "what we currently have (video frames, live timing, coarse OpenF1)",
  "required_telemetry_evidence": [
    {{
      "id": "steering_apex",
      "label": "High-frequency steering angle 100m→apex",
      "rationale": "why this is needed to sustain the claim",
      "status": "present|pending_phase2|insufficient",
      "phase2_schema_ref": "steering_angle_deg"
    }}
  ],
  "success_probability": "Low|Medium|High",
  "legal_risk_notes": "admissibility / Article 14 new-element risk",
  "recommended_next_step": "what the Team Principal should do next",
  "incident": "one-sentence incident summary",
  "rule_cited": "primary article_name from regulatory_violations",
  "telemetry_facts": "only numbers that appear in the telemetry summary",
  "verdict": "Protestable claim | Insufficient evidence for Protest | Right of Review candidate | No further action recommended",
  "penalty": "sought outcome if protest succeeds, or None"
}}

STRICT DIRECTIVES:
- Extract EXACT verbatim quotes from the RAG context into exact_quote. Do NOT paraphrase rules.
- Copy page_number and source_document from chunk metadata into each regulatory_violations item.
- If micro-telemetry (e.g. Turn 5 steering angle) is missing from OpenF1, flag it in
  required_telemetry_evidence with status pending_phase2 for Phase 2 ingestion.
- Never invent speed, brake, throttle, or steering values that are not in the telemetry summary.
- Prefer Article 13 Protest language when evidence is incomplete but the claim is specific;
  prefer Article 14 Right of Review language when an original decision already exists and a
  significant new element is missing.
- success_probability must be Low when required micro-telemetry is pending.
"""


class StewardState(TypedDict, total=False):
    clip_url: Optional[str]
    clip_data_url: Optional[str]
    year: Optional[int]
    circuit: Optional[str]
    meeting_key: Optional[int]
    session_key: Optional[int]
    incident_hint: str
    live_feed: Dict[str, Any]
    filing_team: str
    filing_type: str
    session_type: Optional[str]
    lap_number: Optional[int]
    involved_driver_numbers: List[int]
    spatial_description: str
    vision: Dict[str, Any]
    telemetry_summary: str
    telemetry_series: List[Dict[str, Any]]
    telemetry_degraded: bool
    session_key_resolved: Optional[int]
    retrieved_rules: List[Dict[str, Any]]
    verdict: Dict[str, str]
    protest_dossier: Dict[str, Any]
    pipeline: List[Dict[str, Any]]
    errors: List[str]
    assumptions: List[str]


def extract_json_object(text: str) -> Dict[str, Any]:
    raw = (text or "").strip()
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.S | re.I)
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.S)
    if fenced:
        raw = fenced.group(1)
    else:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            raw = raw[start : end + 1]
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("model did not return a JSON object")
    return data


def _mark(state: StewardState, stage: str, status: str, detail: str = "") -> List[Dict[str, Any]]:
    pipeline = list(state.get("pipeline") or [])
    pipeline.append({"stage": stage, "status": status, "detail": detail})
    return pipeline


def _driver_numbers(value: Any) -> List[int]:
    numbers: List[int] = []
    if not isinstance(value, list):
        return numbers
    for item in value:
        try:
            number = int(item)
        except (TypeError, ValueError):
            continue
        if 1 <= number <= 99:
            numbers.append(number)
    seen = []
    for number in numbers:
        if number not in seen:
            seen.append(number)
    return seen


def _normalize_vision(payload: Dict[str, Any], state: StewardState) -> Dict[str, Any]:
    session_type = str(payload.get("session_type") or "Unknown").strip() or "Unknown"
    circuit = str(payload.get("circuit") or "").strip()
    if not circuit or circuit.lower() in {"unknown", "none", "null"}:
        circuit = str(state.get("circuit") or "").strip()
    lap_raw = payload.get("lap_number")
    try:
        lap_number = int(lap_raw) if lap_raw not in (None, "", 0, "0") else None
    except (TypeError, ValueError):
        lap_number = None
    drivers = _driver_numbers(payload.get("involved_driver_numbers"))
    spatial = str(payload.get("spatial_description") or "").strip()
    if not spatial:
        spatial = (state.get("incident_hint") or "").strip() or "Spatial description unavailable from the clip."
    blob = "{0} {1}".format(state.get("incident_hint") or "", spatial)
    if not drivers:
        hint_numbers = re.findall(r"(?:car|driver|#)\s*([1-9][0-9]?)\b", blob, flags=re.I)
        drivers = _driver_numbers([int(item) for item in hint_numbers])
    if lap_number is None:
        lap_match = re.search(r"\blap\s+(\d{1,3})\b", blob, flags=re.I)
        if lap_match:
            lap_number = int(lap_match.group(1))
    if not circuit:
        # Light circuit hint extraction from overlays / operator text.
        for token in (
            "spa",
            "monza",
            "monaco",
            "silverstone",
            "suzuka",
            "bahrain",
            "sakhir",
            "jeddah",
            "melbourne",
            "imola",
            "austin",
            "singapore",
            "interlagos",
            "mexico",
            "hungary",
            "hungaroring",
            "zandvoort",
            "shanghai",
            "miami",
            "las vegas",
            "montreal",
            "barcelona",
            "catalunya",
            "baku",
            "qatar",
            "abu dhabi",
            "yas marina",
        ):
            if re.search(r"\b{0}\b".format(re.escape(token)), blob, flags=re.I):
                circuit = token.title()
                break
    return {
        "circuit": circuit or "Unknown",
        "session_type": session_type,
        "lap_number": lap_number,
        "involved_driver_numbers": drivers,
        "spatial_description": spatial,
    }


def _merge_live_feed(state: StewardState, normalized: Dict[str, Any]) -> Dict[str, Any]:
    """Fill vision gaps from live timing / broadcast overlay (never the steward penalty)."""
    merged = dict(normalized)
    feed = state.get("live_feed") or {}
    assumptions: List[str] = []

    feed_drivers = _driver_numbers(feed.get("involved_driver_numbers"))
    if feed_drivers and not merged.get("involved_driver_numbers"):
        merged["involved_driver_numbers"] = feed_drivers
        assumptions.append("Live feed supplied involved_driver_numbers: {0}.".format(feed_drivers))

    feed_lap = feed.get("lap_number")
    if feed_lap is not None and merged.get("lap_number") is None:
        try:
            merged["lap_number"] = int(feed_lap)
            assumptions.append("Live feed supplied lap_number={0}.".format(merged["lap_number"]))
        except (TypeError, ValueError):
            pass

    feed_session = str(feed.get("session_type") or "").strip()
    if feed_session and (merged.get("session_type") or "Unknown") in {"Unknown", ""}:
        merged["session_type"] = feed_session
        assumptions.append("Live feed supplied session_type={0}.".format(feed_session))

    timing_note = str(feed.get("timing_note") or "").strip()
    if timing_note:
        spatial = str(merged.get("spatial_description") or "").strip()
        if timing_note.lower() not in spatial.lower():
            merged["spatial_description"] = "{0} {1}".format(timing_note, spatial).strip()
        assumptions.append("Merged live timing note into spatial description.")

    # Forward vision-identified circuit into graph state for OpenF1 session resolve.
    vision_circuit = str(merged.get("circuit") or "").strip()
    if vision_circuit and vision_circuit.lower() not in {"unknown", "none", ""}:
        if not (state.get("circuit") or "").strip():
            merged["circuit_from_vision"] = vision_circuit
            assumptions.append("Vision supplied circuit={0}.".format(vision_circuit))

    if assumptions:
        merged["live_feed_assumptions"] = assumptions
    return merged


def _fallback_vision(state: StewardState, reason: str) -> Dict[str, Any]:
    hint = (state.get("incident_hint") or "").strip()
    normalized = _normalize_vision(
        {
            "circuit": state.get("circuit") or "Unknown",
            "session_type": "Unknown",
            "lap_number": None,
            "involved_driver_numbers": [],
            "spatial_description": hint or "Vision model unavailable; no spatial extract from the clip.",
        },
        state,
    )
    normalized["degraded"] = True
    normalized["reason"] = reason
    return normalized


def _openrouter_headers() -> Dict[str, str]:
    return {
        "Authorization": "Bearer {0}".format(settings.openrouter_key),
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/apex-analytics-steward",
        "X-Title": "Apex Analytics Race Steward",
    }


def _is_video_media(media: str) -> bool:
    lowered = media.split("?", 1)[0].lower()
    return media.startswith("data:video/") or lowered.endswith((".mp4", ".webm", ".mov", ".mkv"))


def _is_image_media(media: str) -> bool:
    lowered = media.split("?", 1)[0].lower()
    return media.startswith("data:image/") or lowered.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))


def _decode_data_url(media: str) -> Tuple[bytes, str]:
    header, encoded = media.split(",", 1)
    mime = header.split(";", 1)[0].split(":", 1)[1]
    return base64.b64decode(encoded), mime


def _extract_frame_data_urls_from_bytes(payload: bytes, max_frames: int = 4) -> List[str]:
    try:
        import cv2
    except ImportError:
        return []
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as tmp:
        tmp.write(payload)
        tmp.flush()
        cap = cv2.VideoCapture(tmp.name)
        if not cap.isOpened():
            cap.release()
            return []
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if frame_count <= 0:
            cap.release()
            return []
        indices = sorted(
            {
                max(0, min(frame_count - 1, int(frame_count * pct)))
                for pct in (0.12, 0.32, 0.52, 0.72, 0.88)
            }
        )[:max_frames]
        urls: List[str] = []
        for index in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, index)
            ok, frame = cap.read()
            if not ok:
                continue
            ok, encoded = cv2.imencode(".jpg", frame)
            if not ok:
                continue
            b64 = base64.b64encode(encoded.tobytes()).decode("ascii")
            urls.append("data:image/jpeg;base64,{0}".format(b64))
        cap.release()
        return urls


def _media_to_image_data_urls(media: str) -> List[str]:
    if _is_image_media(media):
        return [media]
    if not _is_video_media(media):
        return []
    if media.startswith("data:"):
        payload, _mime = _decode_data_url(media)
        return _extract_frame_data_urls_from_bytes(payload)
    parsed = urlparse(media)
    if parsed.scheme in {"http", "https"}:
        try:
            response = httpx.get(media, timeout=60.0, follow_redirects=True)
            response.raise_for_status()
            return _extract_frame_data_urls_from_bytes(response.content)
        except Exception:
            return []
    return []


def _vision_content(state: StewardState) -> List[Dict[str, Any]]:
    prompt = VISION_PROMPT.format(
        year=state.get("year") or "unknown",
        circuit=state.get("circuit") or "unknown",
        hint=(state.get("incident_hint") or "none"),
    )
    content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
    clip_url = (state.get("clip_url") or "").strip()
    data_url = (state.get("clip_data_url") or "").strip()
    media = data_url or clip_url
    if not media:
        return content
    image_urls = _media_to_image_data_urls(media)
    if not image_urls and _is_video_media(media):
        content[0]["text"] = (
            prompt
            + "\n\nNote: video frame extraction failed (install opencv-python-headless). Describe from metadata only if visible in filenames."
        )
        return content
    for image_url in image_urls:
        content.append({"type": "image_url", "image_url": {"url": image_url}})
    if len(image_urls) > 1:
        content[0]["text"] = (
            prompt
            + "\n\nYou are receiving {0} still frames sampled across the clip timeline. Infer the incident from the sequence.".format(
                len(image_urls)
            )
        )
    return content


async def default_vision_complete(state: StewardState) -> Dict[str, Any]:
    if not settings.openrouter_key:
        return _fallback_vision(state, "OPENROUTER_API_KEY is not configured")
    if not (state.get("clip_url") or state.get("clip_data_url") or state.get("incident_hint")):
        return _fallback_vision(state, "no clip or incident hint")
    body = {
        "model": settings.steward_vision_model,
        "messages": [{"role": "user", "content": _vision_content(state)}],
        "temperature": 0,
    }
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            "{0}/chat/completions".format(settings.openrouter_base_url.rstrip("/")),
            headers=_openrouter_headers(),
            json=body,
        )
        response.raise_for_status()
        payload = response.json()
    message = (((payload.get("choices") or [{}])[0]).get("message") or {}).get("content") or ""
    parsed = extract_json_object(str(message))
    return _normalize_vision(parsed, state)


async def default_reason_complete(state: StewardState) -> Dict[str, Any]:
    if not settings.openrouter_key:
        return _heuristic_dossier(state, "OPENROUTER_API_KEY is not configured")
    rules_text = "\n\n".join(
        (
            "#{0} {1}\n"
            "source_document={2} page_number={3}\n"
            "{4}"
        ).format(
            item.get("id"),
            item.get("title") or item.get("article") or "",
            item.get("source_document") or item.get("source") or "",
            item.get("page_number") if item.get("page_number") is not None else 0,
            item.get("text") or "",
        )
        for item in (state.get("retrieved_rules") or [])
    ) or "(no rules retrieved)"
    body = {
        "model": settings.steward_reason_model,
        "messages": [
            {
                "role": "user",
                "content": REASON_PROMPT.format(
                    filing_team=state.get("filing_team") or "Mercedes-AMG Petronas Formula One Team",
                    filing_type=state.get("filing_type") or "protest",
                    vision=json.dumps(state.get("vision") or {}, indent=2),
                    telemetry=state.get("telemetry_summary") or "Telemetry unavailable.",
                    rules=rules_text,
                ),
            }
        ],
        "temperature": 0,
    }
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            "{0}/chat/completions".format(settings.openrouter_base_url.rstrip("/")),
            headers=_openrouter_headers(),
            json=body,
        )
        response.raise_for_status()
        payload = response.json()
    message = (((payload.get("choices") or [{}])[0]).get("message") or {}).get("content") or ""
    parsed = extract_json_object(str(message))
    return _normalize_dossier(parsed, state)


def _default_phase2_evidence(state: StewardState) -> List[Dict[str, Any]]:
    spatial = (state.get("spatial_description") or "").lower()
    turn_hint = "Turn apex"
    for token in ("turn 5", "turn 1", "les combes", "pouhon", "la source"):
        if token in spatial:
            turn_hint = token.title()
            break
    return [
        {
            "id": "steering_apex",
            "label": "High-frequency steering angle ({0}: 100m board → apex)".format(turn_hint),
            "rationale": "Required to prove understeer / corrective lock vs intentional squeeze.",
            "status": "pending_phase2",
            "phase2_schema_ref": "steering_angle_deg",
        },
        {
            "id": "brake_apex",
            "label": "Brake pressure / longitudinal G at turn-in",
            "rationale": "Separates late braking from front-end grip loss into the other car.",
            "status": "pending_phase2",
            "phase2_schema_ref": "brake_pressure_bar",
        },
        {
            "id": "throttle_delta",
            "label": "Throttle lift delta between involved cars",
            "rationale": "Shows whether the defending car lifted enough to leave racing room.",
            "status": "pending_phase2",
            "phase2_schema_ref": "throttle_pct",
        },
        {
            "id": "tcam_sync",
            "label": "Onboard T-Cam synchronized to the same timestamps",
            "rationale": "Article 14 new-element candidate; corroborates contact / overlap at apex.",
            "status": "pending_phase2",
            "phase2_schema_ref": "onboard_tcam_url",
        },
    ]


def _mark_present_evidence(items: List[Dict[str, Any]], state: StewardState) -> List[Dict[str, Any]]:
    has_coarse = bool(state.get("telemetry_series")) and not state.get("telemetry_degraded")
    out = []
    for item in items:
        row = dict(item)
        status = str(row.get("status") or "pending_phase2")
        ref = str(row.get("phase2_schema_ref") or "")
        if has_coarse and ref in {"speed_kph", "throttle_pct"} and status == "pending_phase2":
            # Coarse OpenF1 may partially cover speed/throttle but not micro-window claims.
            row["status"] = "insufficient"
            row["rationale"] = (
                "{0} Coarse OpenF1 samples are present but not apex-window dense.".format(
                    row.get("rationale") or ""
                )
            ).strip()
        out.append(row)
    if has_coarse:
        out.insert(
            0,
            {
                "id": "openf1_car_data",
                "label": "OpenF1 car_data (speed / brake / throttle)",
                "rationale": "Bound for involved drivers; useful for preliminary dossier only.",
                "status": "present",
                "phase2_schema_ref": "speed_kph",
            },
        )
    if state.get("spatial_description"):
        out.insert(
            0,
            {
                "id": "broadcast_vision",
                "label": "Broadcast / clip spatial extract",
                "rationale": "Vision node description of geometry and contact.",
                "status": "present",
                "phase2_schema_ref": "",
            },
        )
    return out


def _default_citations(state: StewardState) -> List[Dict[str, Any]]:
    rules = state.get("retrieved_rules") or []
    citations: List[Dict[str, Any]] = []
    for rule in rules[:3]:
        if not isinstance(rule, dict):
            continue
        text = str(rule.get("text") or "").strip()
        title = str(rule.get("title") or rule.get("id") or "FIA Sporting Regulations").strip()
        if not text and not title:
            continue
        try:
            page = int(rule.get("page_number") or 0)
        except (TypeError, ValueError):
            page = 0
        source = str(
            rule.get("source_document") or rule.get("source") or "fia_driving_standards.md"
        ).strip()
        citations.append(
            {
                "article_name": title[:160],
                "exact_quote": (text or title)[:600],
                "page_number": page,
                "source_document": source,
            }
        )
    if citations:
        return citations
    return [
        {
            "article_name": "ISC Appendix L, Chapter IV, Article 2 d)",
            "exact_quote": (
                "Causing a collision — a driver must not cause a collision or force another "
                "driver off the track (teaching corpus)."
            ),
            "page_number": 0,
            "source_document": "fia_driving_standards.md",
        },
        {
            "article_name": "ISC Article 13 — Protests",
            "exact_quote": (
                "A Protest may be lodged when a competitor alleges a breach of the regulations "
                "(teaching corpus)."
            ),
            "page_number": 0,
            "source_document": "fia_driving_standards.md",
        },
        {
            "article_name": "ISC Article 14 — Right of Review",
            "exact_quote": (
                "A Right of Review may be sought where a significant and relevant new element "
                "is discovered (teaching corpus)."
            ),
            "page_number": 0,
            "source_document": "fia_driving_standards.md",
        },
    ]


def _normalize_citations(raw: Any, state: StewardState) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    rules = [r for r in (state.get("retrieved_rules") or []) if isinstance(r, dict)]
    for index, item in enumerate(raw):
        if isinstance(item, str) and item.strip():
            meta = rules[index] if index < len(rules) else (rules[0] if rules else {})
            try:
                page = int(meta.get("page_number") or 0)
            except (TypeError, ValueError):
                page = 0
            out.append(
                {
                    "article_name": item.strip()[:160],
                    "exact_quote": item.strip()[:600],
                    "page_number": page,
                    "source_document": str(
                        meta.get("source_document") or meta.get("source") or "teaching_corpus"
                    ),
                }
            )
            continue
        if not isinstance(item, dict):
            continue
        article = str(item.get("article_name") or item.get("title") or "").strip()
        quote = str(item.get("exact_quote") or item.get("quote") or item.get("text") or "").strip()
        if not article and not quote:
            continue
        try:
            page = int(item.get("page_number") or 0)
        except (TypeError, ValueError):
            page = 0
        source = str(item.get("source_document") or item.get("source") or "").strip()
        if not source and rules:
            source = str(rules[0].get("source_document") or rules[0].get("source") or "")
        out.append(
            {
                "article_name": (article or "FIA regulation")[:160],
                "exact_quote": (quote or article)[:600],
                "page_number": page,
                "source_document": source or "teaching_corpus",
            }
        )
    return out


def _normalize_dossier(payload: Dict[str, Any], state: StewardState) -> Dict[str, Any]:
    evidence_raw = payload.get("required_telemetry_evidence")
    if not isinstance(evidence_raw, list) or not evidence_raw:
        evidence_raw = _default_phase2_evidence(state)
    evidence = []
    for index, item in enumerate(evidence_raw):
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "pending_phase2")
        if status not in {"present", "pending_phase2", "insufficient"}:
            status = "pending_phase2"
        evidence.append(
            {
                "id": str(item.get("id") or "evidence-{0}".format(index)),
                "label": str(item.get("label") or "").strip(),
                "rationale": str(item.get("rationale") or "").strip(),
                "status": status,
                "phase2_schema_ref": str(item.get("phase2_schema_ref") or "").strip(),
            }
        )
    evidence = _mark_present_evidence(evidence, state)

    pending = [item for item in evidence if item.get("status") != "present"]
    probability = str(payload.get("success_probability") or "").strip().title()
    if probability not in {"Low", "Medium", "High"}:
        probability = "Low" if pending else "Medium"
    if state.get("telemetry_degraded") or pending:
        probability = "Low" if len(pending) >= 2 else probability
        if probability == "High" and pending:
            probability = "Medium"

    filing_type = str(payload.get("filing_type") or state.get("filing_type") or "protest")
    if filing_type not in {"protest", "right_of_review"}:
        filing_type = "protest"

    violations = _normalize_citations(payload.get("regulatory_violations"), state)
    if not violations:
        violations = _default_citations(state)

    primary = str(payload.get("primary_claim") or "").strip()
    if not primary:
        primary = state.get("spatial_description") or "Incident claim could not be formalized."

    dossier = {
        "filing_type": filing_type,
        "filing_team": str(
            payload.get("filing_team") or state.get("filing_team") or "Mercedes-AMG Petronas Formula One Team"
        ),
        "competitor_team": str(payload.get("competitor_team") or "").strip(),
        "primary_claim": primary,
        "regulatory_violations": violations,
        "available_evidence_summary": str(
            payload.get("available_evidence_summary")
            or state.get("telemetry_summary")
            or "Vision and teaching-corpus only."
        ).strip(),
        "required_telemetry_evidence": evidence,
        "success_probability": probability,
        "legal_risk_notes": str(payload.get("legal_risk_notes") or "").strip()
        or (
            "Without apex-window micro-telemetry, stewards may treat the filing as a re-argument "
            "of existing broadcast evidence (Article 14 significance risk)."
        ),
        "recommended_next_step": str(payload.get("recommended_next_step") or "").strip()
        or "Ingest Phase 2 high-frequency telemetry before lodging the Protest.",
        "phase2_bridge": (
            "Ingest high-frequency micro-telemetry via POST /api/steward/phase2/telemetry "
            "to satisfy pending evidentiary items before lodging with the FIA."
        ),
    }

    # Legacy verdict summary for older UI / tests.
    first_cite = violations[0] if violations else {}
    rule_fallback = "{0}".format(first_cite.get("article_name") or "")
    verdict = {
        "incident": str(payload.get("incident") or primary)[:400],
        "rule_cited": str(payload.get("rule_cited") or rule_fallback).strip(),
        "telemetry_facts": str(payload.get("telemetry_facts") or state.get("telemetry_summary") or "").strip(),
        "verdict": str(payload.get("verdict") or "Insufficient evidence for Protest").strip(),
        "penalty": str(payload.get("penalty") or "None").strip(),
    }
    return {"protest_dossier": dossier, "verdict": verdict}


def _heuristic_dossier(state: StewardState, reason: str) -> Dict[str, Any]:
    spatial = state.get("spatial_description") or ""
    degraded = bool(state.get("telemetry_degraded"))
    drivers = state.get("involved_driver_numbers") or []
    claim = spatial[:320] or "Incident could not be reconstructed from available media."
    if drivers and len(drivers) >= 2:
        claim = (
            "Formal allegation: Car {0} failed to leave racing room / caused contact with Car {1}. {2}"
        ).format(drivers[0], drivers[1], spatial[:200])

    evidence = _mark_present_evidence(_default_phase2_evidence(state), state)
    probability = "Low"
    if not degraded and drivers:
        probability = "Medium"

    filing_type = state.get("filing_type") or "protest"
    return _normalize_dossier(
        {
            "filing_type": filing_type,
            "filing_team": state.get("filing_team"),
            "primary_claim": claim,
            "regulatory_violations": _default_citations(state),
            "available_evidence_summary": state.get("telemetry_summary") or "Vision + teaching corpus only.",
            "required_telemetry_evidence": evidence,
            "success_probability": probability,
            "legal_risk_notes": "Heuristic dossier ({0}).".format(reason),
            "recommended_next_step": "Collect Phase 2 micro-telemetry before lodging.",
            "incident": claim,
            "rule_cited": "ISC Appendix L, Chapter IV, Article 2 d) (teaching paraphrase)",
            "telemetry_facts": state.get("telemetry_summary") or "Telemetry unavailable.",
            "verdict": "Insufficient evidence for Protest" if degraded else "Protestable claim",
            "penalty": "5 second time penalty (sought)" if drivers else "None",
        },
        state,
    )


def _normalize_verdict(payload: Dict[str, Any]) -> Dict[str, str]:
    """Backward-compatible wrapper; prefer _normalize_dossier."""
    if "primary_claim" in payload or "required_telemetry_evidence" in payload:
        return _normalize_dossier(payload, {})["verdict"]  # type: ignore[arg-type]
    out = dict(EMPTY_VERDICT)
    for key in EMPTY_VERDICT:
        value = payload.get(key)
        out[key] = "" if value is None else str(value).strip()
    return out


def _heuristic_verdict(state: StewardState, reason: str) -> Dict[str, str]:
    return _heuristic_dossier(state, reason)["verdict"]


def _session_type_candidates(raw: Optional[str]) -> List[str]:
    value = (raw or "").strip().lower()
    if value in {"qualifying", "quali", "q1", "q2", "q3"}:
        return ["Qualifying", "Sprint Qualifying"]
    if "sprint" in value:
        return ["Sprint", "Sprint Shootout"]
    if value in {"practice", "fp1", "fp2", "fp3"}:
        return ["Practice 1", "Practice 2", "Practice 3"]
    return ["Race"]


def _downsample(rows: List[Dict[str, Any]], limit: int = 40) -> List[Dict[str, Any]]:
    if len(rows) <= limit:
        return rows
    step = max(1, len(rows) // limit)
    sampled = rows[::step][:limit]
    if sampled[-1] is not rows[-1]:
        sampled[-1] = rows[-1]
    return sampled


def _metric_delta(rows: List[Dict[str, Any]], field: str) -> Optional[str]:
    values = []
    for row in rows:
        try:
            values.append(float(row.get(field)))
        except (TypeError, ValueError):
            continue
    if len(values) < 2:
        return None
    peak = max(values)
    floor = min(values)
    return "{0:.0f}→{1:.0f} (span {2:.0f})".format(values[0], values[-1], peak - floor)


async def _resolve_session_key(client: Any, state: StewardState, vision: Dict[str, Any]) -> Tuple[Optional[int], List[str]]:
    assumptions: List[str] = []
    existing = state.get("session_key")
    if existing:
        return int(existing), assumptions
    year = state.get("year")
    if year is None:
        assumptions.append("No year supplied; cannot resolve OpenF1 session_key.")
        return None, assumptions
    try:
        sessions = await client.list_sessions(year=int(year))
    except OpenF1HTTPError as exc:
        assumptions.append("OpenF1 sessions lookup failed: {0}".format(exc.message[:180]))
        return None, assumptions
    meeting_key = state.get("meeting_key")
    circuit = (state.get("circuit") or "").strip().lower()
    wanted_types = _session_type_candidates(str(vision.get("session_type") or ""))
    ranked: List[Tuple[int, Dict[str, Any]]] = []
    for session in sessions or []:
        if meeting_key is not None and session.get("meeting_key") not in (meeting_key, int(meeting_key)):
            continue
        circuit_name = str(session.get("circuit_short_name") or session.get("location") or "").lower()
        meeting_name = str(session.get("meeting_name") or session.get("country_name") or "").lower()
        if circuit and circuit not in circuit_name and circuit not in meeting_name:
            continue
        session_name = str(session.get("session_name") or session.get("session_type") or "")
        score = 2 if session_name in wanted_types else 0
        if session_name.lower() == "race":
            score += 1
        ranked.append((score, session))
    ranked.sort(key=lambda item: item[0], reverse=True)
    if not ranked:
        assumptions.append("No OpenF1 session matched year/circuit/session_type.")
        return None, assumptions
    chosen = ranked[0][1]
    key = chosen.get("session_key")
    if key is None:
        return None, assumptions
    assumptions.append("Resolved session_key={0} ({1}).".format(key, chosen.get("session_name") or chosen.get("session_type")))
    return int(key), assumptions


async def _lap_window(client: Any, session_key: int, driver_number: int, lap_number: Optional[int]) -> Dict[str, Any]:
    try:
        laps = await client.get_laps(session_key=session_key, driver_number=driver_number)
    except OpenF1HTTPError:
        laps = []
    if lap_number is not None:
        laps = [row for row in laps if row.get("lap_number") == lap_number]
    if not laps:
        return {}
    lap = laps[0]
    start = str(lap.get("date_start") or "") or None
    duration = lap.get("lap_duration")
    end = None
    if start and duration:
        try:
            parsed = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
            end = (parsed + timedelta(seconds=float(duration))).astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError):
            end = None
    return {"date_start": start, "date_end": end, "lap": lap}


def _filter_window(rows: List[Dict[str, Any]], window: Dict[str, Any]) -> List[Dict[str, Any]]:
    start = window.get("date_start")
    end = window.get("date_end")
    if not start and not end:
        return rows[:80]
    out = []
    for row in rows:
        stamp = str(row.get("date") or "")
        if start and stamp < str(start):
            continue
        if end and stamp > str(end):
            continue
        out.append(row)
    return out[:400]


async def _fetch_driver_telemetry(
    client: Any,
    session_key: int,
    driver_number: int,
    window: Dict[str, Any],
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"session_key": session_key, "driver_number": driver_number}
    if window.get("date_start"):
        params["date>="] = window["date_start"]
    if window.get("date_end"):
        params["date<="] = window["date_end"]
    try:
        car_data = await client.get_car_data(**params)
    except OpenF1HTTPError as exc:
        if exc.status_code == 401:
            raise
        car_data = []
    if not car_data and ("date>=" in params or "date<=" in params):
        try:
            car_data = await client.get_car_data(session_key=session_key, driver_number=driver_number)
        except OpenF1HTTPError:
            car_data = []
        car_data = _filter_window(car_data, window)
    try:
        location = await client.get_location(**params)
    except OpenF1HTTPError:
        location = []
    car_data = sorted(car_data, key=lambda row: str(row.get("date") or ""))
    samples = []
    for index, row in enumerate(_downsample(car_data)):
        samples.append(
            {
                "t": index,
                "date": row.get("date"),
                "speed": row.get("speed"),
                "brake": row.get("brake"),
                "throttle": row.get("n_throttle") if row.get("n_throttle") is not None else row.get("throttle"),
            }
        )
    return {"car_data": car_data, "location": location or [], "samples": samples}


def _summarize_telemetry(series: List[Dict[str, Any]], degraded_reason: Optional[str]) -> str:
    if degraded_reason:
        return "Telemetry unavailable: {0}. Reason using vision extract and teaching-corpus rules only.".format(
            degraded_reason
        )
    if not series:
        return "Telemetry unavailable: OpenF1 returned no car_data/location rows for the inferred lap window."
    lines: List[str] = []
    for item in series:
        driver = item.get("driver_number")
        samples = item.get("samples") or []
        speed = _metric_delta(samples, "speed")
        brake = _metric_delta(samples, "brake")
        throttle = _metric_delta(samples, "throttle")
        loc_n = item.get("location_points") or 0
        lines.append(
            "Driver {0}: samples={1}, speed {2}, brake {3}, throttle {4}, location_points={5}.".format(
                driver,
                len(samples),
                speed or "n/a",
                brake or "n/a",
                throttle or "n/a",
                loc_n,
            )
        )
    return " ".join(lines)


def build_steward_graph(
    *,
    openf1: Any = None,
    retrieve_fn: Optional[RetrieveFn] = None,
    vision_fn: Optional[VisionFn] = None,
    reason_fn: Optional[ReasonFn] = None,
):
    retrieve = retrieve_fn or (lambda query, top_k=4: default_retrieve_rules(query, top_k=top_k))
    vision_complete = vision_fn or default_vision_complete
    reason_complete = reason_fn or default_reason_complete

    def _client() -> Any:
        if openf1 is not None:
            return openf1
        from app.runtime import get_client

        return get_client()

    async def vision_extraction_node(state: StewardState) -> dict:
        try:
            vision = await vision_complete(state)
        except Exception as exc:
            vision = _fallback_vision(state, str(exc)[:240])
        normalized = _normalize_vision(vision, state)
        normalized = _merge_live_feed(state, normalized)
        assumptions = list(state.get("assumptions") or [])
        assumptions.extend(normalized.pop("live_feed_assumptions", []) or [])
        if vision.get("degraded"):
            assumptions.append("Vision degraded: {0}".format(vision.get("reason") or "unknown"))
        return {
            "vision": normalized,
            "session_type": normalized.get("session_type"),
            "lap_number": normalized.get("lap_number"),
            "involved_driver_numbers": normalized.get("involved_driver_numbers") or [],
            "spatial_description": normalized.get("spatial_description") or "",
            "circuit": (
                normalized.get("circuit_from_vision")
                or (
                    normalized.get("circuit")
                    if str(normalized.get("circuit") or "").lower() not in {"", "unknown"}
                    else None
                )
                or state.get("circuit")
            ),
            "pipeline": _mark(state, "vision", "done", (normalized.get("spatial_description") or "")[:180]),
            "assumptions": assumptions,
            "errors": list(state.get("errors") or []),
        }

    async def telemetry_fetch_node(state: StewardState) -> dict:
        assumptions = list(state.get("assumptions") or [])
        errors = list(state.get("errors") or [])
        vision = state.get("vision") or {}
        drivers = list(state.get("involved_driver_numbers") or [])
        series: List[Dict[str, Any]] = []
        degraded_reason: Optional[str] = None
        session_key = None
        try:
            client = _client()
            session_key, extra = await _resolve_session_key(client, state, vision)
            assumptions.extend(extra)
            if session_key is None:
                degraded_reason = extra[-1] if extra else "session_key could not be resolved"
            else:
                if not drivers:
                    degraded_reason = "Vision did not yield involved_driver_numbers."
                    assumptions.append(degraded_reason)
                for driver_number in drivers[:4]:
                    window = await _lap_window(client, session_key, driver_number, state.get("lap_number"))
                    if not window and state.get("lap_number"):
                        assumptions.append(
                            "No OpenF1 lap row for driver {0} lap {1}; using session slice.".format(
                                driver_number, state.get("lap_number")
                            )
                        )
                    packed = await _fetch_driver_telemetry(client, session_key, driver_number, window)
                    series.append(
                        {
                            "driver_number": driver_number,
                            "samples": packed["samples"],
                            "location_points": len(packed["location"]),
                        }
                    )
                if drivers and not any(item.get("samples") for item in series):
                    degraded_reason = "OpenF1 car_data empty for the inferred lap window."
        except OpenF1HTTPError as exc:
            if exc.status_code == 401:
                degraded_reason = "F1_LIVE_LOCK: live session blocked OpenF1 telemetry."
            else:
                degraded_reason = "OpenF1 error {0}: {1}".format(exc.status_code, exc.message[:160])
            errors.append(degraded_reason)
        except Exception as exc:
            degraded_reason = "Telemetry node failed: {0}".format(str(exc)[:200])
            errors.append(degraded_reason)

        degraded = bool(degraded_reason) or not any(item.get("samples") for item in series)
        summary = _summarize_telemetry(series, degraded_reason if degraded else None)

        # Enrich context pack with race_control + team_radio (Phase 2 OpenF1 tools).
        race_control_rows: List[Dict[str, Any]] = []
        team_radio_rows: List[Dict[str, Any]] = []
        if session_key is not None:
            try:
                from app.tools.openf1 import get_race_control, get_team_radio, summarize_race_control, summarize_team_radio

                race_control_rows = await get_race_control(
                    int(session_key),
                    state.get("lap_number"),
                    openf1=_client(),
                )
                for driver_number in drivers[:4]:
                    team_radio_rows.extend(
                        await get_team_radio(int(session_key), int(driver_number), openf1=_client())
                    )
                summary = "{0} {1} {2}".format(
                    summary,
                    summarize_race_control(race_control_rows),
                    summarize_team_radio(team_radio_rows),
                ).strip()
            except Exception as exc:
                assumptions.append("OpenF1 race_control/team_radio enrich failed: {0}".format(str(exc)[:160]))

        return {
            "session_key_resolved": session_key,
            "telemetry_series": series,
            "telemetry_summary": summary,
            "telemetry_degraded": degraded,
            "pipeline": _mark(state, "telemetry", "done", "degraded" if degraded else "drivers {0}".format(drivers)),
            "assumptions": assumptions,
            "errors": errors,
        }

    async def verdict_reasoning_node(state: StewardState) -> dict:
        assumptions = list(state.get("assumptions") or [])
        errors = list(state.get("errors") or [])
        query = " ".join(
            part
            for part in (
                state.get("spatial_description") or "",
                str(state.get("session_type") or ""),
                (state.get("incident_hint") or ""),
                "Article 13 Protest Article 14 Right of Review Appendix L Chapter IV",
            )
            if part
        )
        try:
            rules = retrieve(query or "leaving room overtaking collision protest review", 6)
        except Exception as exc:
            rules = []
            errors.append("RAG failed: {0}".format(str(exc)[:180]))
            assumptions.append("Rules retrieval failed; reasoning without vector hits.")
        if not rules:
            assumptions.append("RAG returned no chunks; using empty rule pack.")
        pipeline = _mark(state, "rules", "done", "{0} chunks".format(len(rules)))
        merged: StewardState = dict(state)
        merged["retrieved_rules"] = rules
        merged["pipeline"] = pipeline
        try:
            packed = await reason_complete(merged)
            if "protest_dossier" not in packed:
                packed = _normalize_dossier(packed, merged)
        except Exception as exc:
            errors.append("Reasoner failed: {0}".format(str(exc)[:180]))
            packed = _heuristic_dossier(merged, str(exc)[:120])
        dossier = packed.get("protest_dossier") or {}
        verdict = packed.get("verdict") or {}
        if not dossier.get("primary_claim"):
            packed = _heuristic_dossier(merged, "empty model dossier")
            dossier = packed["protest_dossier"]
            verdict = packed["verdict"]
        if merged.get("telemetry_degraded"):
            facts = verdict.get("telemetry_facts") or ""
            if facts and not re.search(r"unavailable|degraded|not available|no car_data|coarse", facts, re.I):
                verdict["telemetry_facts"] = (
                    "{0} OpenF1 telemetry was coarse or unavailable for an apex-window proof.".format(facts)
                ).strip()
            # Ensure Phase 2 items stay pending when telemetry is degraded.
            evidence = list(dossier.get("required_telemetry_evidence") or [])
            for item in evidence:
                if item.get("status") == "present" and item.get("id") not in {
                    "broadcast_vision",
                    "openf1_car_data",
                }:
                    item["status"] = "pending_phase2"
            dossier["required_telemetry_evidence"] = evidence
            dossier["success_probability"] = "Low"
        pipeline = _mark(merged, "reasoning", "done", dossier.get("success_probability") or "")
        return {
            "retrieved_rules": rules,
            "verdict": verdict,
            "protest_dossier": dossier,
            "pipeline": pipeline,
            "assumptions": assumptions,
            "errors": errors,
        }

    graph = StateGraph(StewardState)
    graph.add_node("vision_extraction", vision_extraction_node)
    graph.add_node("telemetry_fetch", telemetry_fetch_node)
    graph.add_node("verdict_reasoning", verdict_reasoning_node)
    graph.add_edge(START, "vision_extraction")
    graph.add_edge("vision_extraction", "telemetry_fetch")
    graph.add_edge("telemetry_fetch", "verdict_reasoning")
    graph.add_edge("verdict_reasoning", END)
    return graph.compile()


compiled_steward_graph = build_steward_graph()


def initial_steward_state(
    *,
    clip_url: Optional[str] = None,
    clip_data_url: Optional[str] = None,
    year: Optional[int] = None,
    circuit: Optional[str] = None,
    meeting_key: Optional[int] = None,
    session_key: Optional[int] = None,
    incident_hint: str = "",
    live_feed: Optional[Dict[str, Any]] = None,
    filing_team: str = "Mercedes-AMG Petronas Formula One Team",
    filing_type: str = "protest",
) -> StewardState:
    return {
        "clip_url": clip_url,
        "clip_data_url": clip_data_url,
        "year": year,
        "circuit": circuit,
        "meeting_key": meeting_key,
        "session_key": session_key,
        "incident_hint": incident_hint or "",
        "live_feed": live_feed or {},
        "filing_team": filing_team or "Mercedes-AMG Petronas Formula One Team",
        "filing_type": filing_type if filing_type in {"protest", "right_of_review"} else "protest",
        "involved_driver_numbers": [],
        "spatial_description": "",
        "vision": {},
        "telemetry_summary": "",
        "telemetry_series": [],
        "telemetry_degraded": False,
        "retrieved_rules": [],
        "verdict": dict(EMPTY_VERDICT),
        "protest_dossier": {},
        "pipeline": [],
        "errors": [],
        "assumptions": [],
    }
