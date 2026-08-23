from __future__ import annotations

import operator
from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph.message import add_messages


class F1DashboardState(TypedDict):
    messages: Annotated[list, add_messages]
    user_query: str
    thread_id: str

    season_year: Optional[int]
    meeting_key: Optional[int]
    circuit_name: Optional[str]

    intent: str
    route: str
    routing_rationale: str

    analysis_plan: list
    selected_tools: list
    tool_calls: Annotated[list, operator.add]
    raw_payloads: Annotated[list, operator.add]
    analysis_notes: list
    missing_inputs: list
    assumptions: list
    synthesis: str
    needs_more_data: bool

    answer: str
    trace: dict
