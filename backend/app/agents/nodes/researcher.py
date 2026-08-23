from typing import Any, Dict

from app.agents.planning import heuristic_researcher_plan
from app.agents.state import F1DashboardState


def researcher_node(state: F1DashboardState) -> Dict[str, Any]:
    return heuristic_researcher_plan(state)
