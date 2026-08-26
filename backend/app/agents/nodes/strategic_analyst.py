from typing import Any, Dict, List

from app.agents.planning import _payloads_by_tool, _year
from app.agents.state import F1DashboardState
from app.services.championship_report import build_championship_report


def _payload_counts(grouped: Dict[str, List[Dict[str, Any]]]) -> str:
    parts = []
    for tool in ("list_sessions", "get_championship_drivers", "get_championship_teams", "get_session_result", "get_laps", "get_drivers"):
        payloads = grouped.get(tool) or []
        total = sum(len(p.get("preview") or []) for p in payloads)
        parts.append("{0}={1}".format(tool, total))
    return "; ".join(parts)


def strategic_analyst_node(state: F1DashboardState) -> Dict[str, Any]:
    grouped = _payloads_by_tool(state)
    year = _year(state)
    report = build_championship_report(grouped, year)
    notes = list(state.get("analysis_notes") or [])
    leader_points = report.get("leader_points") or 0
    second_points = report.get("second_points") or 0
    remaining_races = report.get("remaining_races") or 0

    notes.append(
        {
            "phase": "identify",
            "detail": "Championship projection for {0}; leader pts={1:.0f}, second pts={2:.0f}, remaining races={3}.".format(
                year or "current season",
                leader_points,
                second_points,
                remaining_races,
            ),
        }
    )
    notes.append(
        {
            "phase": "retrieve",
            "detail": "Tool payload counts: {0}.".format(_payload_counts(grouped)),
        }
    )
    notes.append(
        {
            "phase": "calculate",
            "detail": "Confidence = points-ceiling model (26 pts/weekend) over {0} remaining races, plus sampled wins/DNFs. Ceiling={1:.0f} pts.".format(
                remaining_races,
                remaining_races * 26,
            ),
        }
    )
    notes.append(
        {
            "phase": "result",
            "detail": "Projected {0} at {1:.0f}% confidence.".format(
                report["predicted_winner"],
                (report["confidence"] or 0) * 100,
            ),
        }
    )
    notes.append(
        {
            "phase": "strategy",
            "detail": "Evaluated standings gap, remaining scoring weekends, sampled DNFs, and constructor table.",
        }
    )
    return {
        "synthesis": report["answer"],
        "answer": report["answer"],
        "report_meta": {
            "predicted_winner": report["predicted_winner"],
            "confidence": report["confidence"],
            "key_drivers": report["key_drivers"],
            "contenders": report.get("contenders") or [],
            "follow_ups": report.get("follow_ups") or [],
        },
        "analysis_notes": notes,
        "assumptions": list(state.get("assumptions") or [])
        + [
            "Win probability is a points-ceiling model (26 pts/weekend) plus sampled race form — not a betting market.",
            "DNF rates use retrieved session_result files only, not the full historical archive.",
        ],
    }
