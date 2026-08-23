from typing import Any, Dict

from app.agents.planning import classify_intent, heuristic_analyst_plan
from app.agents.state import F1DashboardState

GENERIC_INTENTS = {"", "unknown", "data_query", "question", "f1_question"}


KNOWN_INTENTS = {
    "chitchat",
    "constructor_finance",
    "driver_roi",
    "meeting_insights",
    "telemetry_compare",
    "research",
    "teammate_h2h",
    "stint_strategy",
    "position_gain",
    "comparative_standings",
    "regulatory_knowledge",
    "historical_out_of_coverage",
}


def data_analyst_node(state: F1DashboardState) -> Dict[str, Any]:
    merged = dict(state)
    # Always re-tokenise from the user question. LLM routers write paragraphs into intent.
    merged["intent"] = classify_intent(state)
    return heuristic_analyst_plan(merged)
