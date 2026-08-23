from typing import Any, Dict, List

from app.agents.state import F1DashboardState

TRACE_KEYS = ("routing", "reasoning_path", "api_calls", "pipelines")


def technical_manager_node(state: F1DashboardState) -> dict:
    route = state.get("route") or "generalist_direct"
    tool_calls = list(state.get("tool_calls") or [])
    reasoning_path: List[Dict[str, Any]] = [
        {
            "step": 1,
            "actor": "generalist",
            "summary": state.get("routing_rationale") or state.get("intent") or "",
        }
    ]
    step = 2
    if route in {"data_analyst", "researcher"}:
        actor = "researcher" if route == "researcher" else "data_analyst"
        reasoning_path.append(
            {
                "step": step,
                "actor": actor,
                "summary": "Plan: {0}".format("; ".join(state.get("analysis_plan") or []) or "none"),
            }
        )
        step += 1
        for call in tool_calls:
            reasoning_path.append(
                {
                    "step": step,
                    "actor": "tools",
                    "summary": "{0}({1}) status={2}".format(
                        call.get("tool"), call.get("params") or call.get("args"), call.get("status")
                    ),
                }
            )
            step += 1
        if state.get("synthesis"):
            reasoning_path.append(
                {
                    "step": step,
                    "actor": actor,
                    "summary": str(state.get("synthesis"))[:240],
                }
            )
            step += 1
        reasoning_path.append(
            {
                "step": step,
                "actor": "inner_monologue",
                "summary": (
                    "I routed as {intent}. I only trust tool payloads in this trace. "
                    "If dollars appear they must come from get_finance_estimates or search_commercial, "
                    "never from the model. Chosen tools: {tools}."
                ).format(
                    intent=state.get("intent") or "unknown",
                    tools=", ".join(sorted({str(c.get("tool")) for c in tool_calls})) or "none",
                ),
            }
        )

    tools_used = {c.get("tool") for c in tool_calls}
    pipelines: List[Dict[str, Any]] = []
    if "list_meetings" in tools_used:
        pipelines.append(
            {
                "name": "resolve_meeting",
                "description": "circuit/season calendar via list_meetings",
            }
        )
    champ_calls = [c for c in tool_calls if c.get("tool") == "get_championship_drivers"]
    if len(champ_calls) >= 2:
        pipelines.append(
            {
                "name": "championship_compare",
                "description": "join championship_drivers on driver_number across race session_keys",
            }
        )
    elif champ_calls:
        pipelines.append(
            {
                "name": "championship_snapshot",
                "description": "single championship_drivers snapshot",
            }
        )
    if "get_race_control" in tools_used:
        pipelines.append(
            {
                "name": "race_control_timeline",
                "description": "session list plus race_control messages for a meeting",
            }
        )
    if "get_laps" in tools_used:
        pipelines.append(
            {
                "name": "pace_compare",
                "description": "laps joined to drivers for the selected session",
            }
        )
    if "get_finance_estimates" in tools_used:
        pipelines.append(
            {
                "name": "finance_fact_store",
                "description": "read cited commercial facts (no live search)",
            }
        )
    if "search_commercial" in tools_used:
        pipelines.append(
            {
                "name": "search_commercial",
                "description": "Researcher web search then write-through to the fact store",
            }
        )

    api_calls = []
    for call in tool_calls:
        api_calls.append(
            {
                "tool": call.get("tool"),
                "method": call.get("method") or "GET",
                "path": call.get("path"),
                "params": call.get("params") or call.get("args") or {},
                "status": call.get("status"),
                "record_count": call.get("record_count"),
                "error": call.get("error"),
            }
        )

    notes = list(state.get("analysis_notes") or [])
    if not notes:
        for call in tool_calls:
            notes.append(
                {
                    "phase": "retrieve",
                    "detail": "{0} status={1} rows={2} params={3}".format(
                        call.get("tool"),
                        call.get("status"),
                        call.get("record_count"),
                        call.get("params") or call.get("args") or {},
                    ),
                }
            )
        if state.get("answer"):
            notes.append({"phase": "result", "detail": str(state.get("answer"))[:280]})

    trace: Dict[str, Any] = {
        "routing": {
            "intent": state.get("intent") or "unknown",
            "chosen_node": route,
            "rationale": state.get("routing_rationale") or "",
        },
        "reasoning_path": reasoning_path,
        "api_calls": api_calls,
        "pipelines": pipelines,
        "execution_trace": notes,
        "missing_inputs": list(state.get("missing_inputs") or []),
        "assumptions": list(state.get("assumptions") or []),
    }
    updates: Dict[str, Any] = {"trace": trace}
    if not (state.get("answer") or "").strip():
        updates["answer"] = "No answer produced; inspect the Technical Manager trace."
    return updates
