from typing import Any, Dict

from app.agents.planning import _payloads_by_tool, _year
from app.agents.state import F1DashboardState
from app.services.championship_report import build_championship_report


def strategic_analyst_node(state: F1DashboardState) -> Dict[str, Any]:
    grouped = _payloads_by_tool(state)
    report = build_championship_report(grouped, _year(state))
    notes = list(state.get("analysis_notes") or [])
    notes.append(
        {
            "phase": "strategy",
            "detail": "Projected {0} at {1:.0f}% from standings gap, remaining scoring weekends, sampled DNFs, and constructor table.".format(
                report["predicted_winner"],
                (report["confidence"] or 0) * 100,
            ),
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
