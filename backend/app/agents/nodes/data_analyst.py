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


DATA_ANALYST_SYSTEM_PROMPT = """You are the F1 Data Analyst.
You have tools: OpenF1/Jolpica for points, laps, telemetry, session results.
You have MOCK_FINANCIAL_DATA (and the commercial fact store) for 2023/2024 estimated
driver salaries and constructor valuations. get_finance_estimates already merges that mock.

Rules:
- Fetch points/telemetry from OpenF1/Jolpica. Never invent championship numbers.
- Cross-reference dollars only from get_finance_estimates / MOCK_FINANCIAL_DATA.
- If a salary or valuation is missing from those sources, say it is missing. Do not guess.
- Always write the arithmetic: Formula: Salary $X / Points Y = FER $Z
  or Formula: Cap $X / Constructor points Y = $Z per point.
"""


def data_analyst_node(state: F1DashboardState) -> Dict[str, Any]:
    merged = dict(state)
    merged["intent"] = classify_intent(state)
    merged["analyst_system_prompt"] = DATA_ANALYST_SYSTEM_PROMPT
    result = heuristic_analyst_plan(merged)
    plan = list(result.get("analysis_plan") or [])
    if DATA_ANALYST_SYSTEM_PROMPT.splitlines()[0] not in " ".join(plan):
        result["analysis_plan"] = [
            "Use OpenF1 for sport data; MOCK_FINANCIAL_DATA/fact store for USD; never invent finance."
        ] + plan
    return result
