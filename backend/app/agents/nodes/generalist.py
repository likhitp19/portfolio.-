from typing import Any, Dict

from app.agents.planning import _year, heuristic_generalist, maybe_llm_generalist
from app.agents.state import F1DashboardState


def generalist_node(state: F1DashboardState) -> Dict[str, Any]:
    heuristic = heuristic_generalist(state)
    # Never let the LLM answer quantitative F1 from weights — skip it for specialist routes.
    if heuristic.get("route") in {"data_analyst", "researcher"}:
        heuristic["season_year"] = _year(state)
        return heuristic
    llm = maybe_llm_generalist(state)
    if not llm:
        heuristic["season_year"] = _year(state)
        return heuristic
    if heuristic.get("intent") in {"regulatory_knowledge", "historical_out_of_coverage"}:
        heuristic["season_year"] = _year(state)
        return heuristic
    if llm.get("route") == "generalist_direct" and not llm.get("answer"):
        llm["answer"] = heuristic.get("answer")
    # DeepSeek often classifies F1 questions as small talk; keep specialist routing.
    if heuristic.get("route") != "generalist_direct" and llm.get("route") == "generalist_direct":
        llm["route"] = heuristic.get("route")
        llm["intent"] = heuristic.get("intent")
        llm["answer"] = ""
        llm["routing_rationale"] = (
            "{0} LLM asked to skip retrieval; heuristic kept {1}.".format(
                heuristic.get("routing_rationale"),
                heuristic.get("route"),
            )
        )
    if heuristic.get("route") == "researcher" and llm.get("route") != "researcher":
        llm["route"] = "researcher"
        llm["intent"] = "research"
        llm["answer"] = ""
        llm["routing_rationale"] = heuristic.get("routing_rationale")
        llm["season_year"] = _year(state)
        return llm
    known = {
        "chitchat",
        "constructor_finance",
        "driver_roi",
        "meeting_insights",
        "telemetry_compare",
        "teammate_h2h",
        "stint_strategy",
        "position_gain",
        "comparative_standings",
        "championship_projection",
        "research",
        "regulatory_knowledge",
        "historical_out_of_coverage",
    }
    if str(llm.get("intent") or "") not in known:
        llm["intent"] = heuristic.get("intent")
        llm["route"] = heuristic.get("route") or llm.get("route")
        llm["answer"] = "" if heuristic.get("route") != "generalist_direct" else (llm.get("answer") or heuristic.get("answer"))
        llm["routing_rationale"] = (
            "{0} LLM intent was free text; heuristic kept {1}.".format(
                heuristic.get("routing_rationale"),
                heuristic.get("intent"),
            )
        )
    specialist = {
        "constructor_finance",
        "driver_roi",
        "meeting_insights",
        "telemetry_compare",
        "teammate_h2h",
        "stint_strategy",
        "position_gain",
    }
    if heuristic.get("intent") in specialist:
        previous = llm.get("intent")
        llm["intent"] = heuristic.get("intent")
        llm["route"] = heuristic.get("route")
        llm["answer"] = ""
        llm["routing_rationale"] = (
            "{0} LLM intent={1} ignored; heuristic kept {2}.".format(
                heuristic.get("routing_rationale"),
                previous,
                heuristic.get("intent"),
            )
        )
    result = llm
    result["season_year"] = _year(state)
    return result
