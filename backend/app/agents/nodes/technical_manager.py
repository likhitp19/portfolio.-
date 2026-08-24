from typing import Any, Dict, List

from app.agents.state import F1DashboardState
from app.agents.tools import SANDBOX_NOTICE

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
        if state.get("intent") == "championship_projection":
            reasoning_path.append(
                {
                    "step": step,
                    "actor": "strategic_analyst",
                    "summary": "Evaluated pace trajectories, DNF risk, remaining scoring weekends, constructor yield, and teammate cushions.",
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
    if "get_session_result" in tools_used:
        pipelines.append(
            {
                "name": "race_classifications",
                "description": "session_result files for finishes and DNF flags",
            }
        )
    if state.get("intent") == "championship_projection":
        pipelines.append(
            {
                "name": "championship_projection",
                "description": "standings + classifications + remaining calendar → title probability",
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
                "duration_ms": call.get("duration_ms"),
                "timestamp": call.get("timestamp"),
                "error": call.get("error"),
            }
        )

    notes = list(state.get("analysis_notes") or [])
    if any(call.get("sandbox_fallback") or SANDBOX_NOTICE in str(call.get("error") or "") for call in tool_calls):
        notes = [{"phase": "notice", "detail": SANDBOX_NOTICE}] + notes
        reasoning_path.append(
            {
                "step": len(reasoning_path) + 1,
                "actor": "technical_manager",
                "summary": SANDBOX_NOTICE,
            }
        )
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

    finance_cards = []
    for note in notes:
        detail = str(note.get("detail") or note.get("detail") or "")
        if "Formula:" in detail:
            finance_cards.append(
                {
                    "formula": detail.split("Formula:", 1)[-1].strip(),
                    "phase": note.get("phase") or "calculate",
                }
            )
            reasoning_path.append(
                {
                    "step": len(reasoning_path) + 1,
                    "actor": "technical_manager",
                    "summary": "Formula: {0}".format(detail.split("Formula:", 1)[-1].strip()),
                }
            )

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
        "finance_cards": finance_cards,
        "agent_handoffs": [
            {"agent": "generalist", "label": "🤖 Generalist Orchestrator: Planning query..."},
            {"agent": "data_analyst", "label": "📊 Data Analyst Agent: Querying race telemetry..."},
            {"agent": "strategic_analyst", "label": "📈 Strategic Analyst: Evaluating pace, reliability, and margins..."},
            {"agent": "technical_manager", "label": "🛠️ Technical Manager: Synthesizing validation trace..."},
        ]
        if (state.get("intent") or "") == "championship_projection"
        else [
            {"agent": "generalist", "label": "🤖 Generalist Orchestrator: Planning query..."},
            {"agent": "data_analyst", "label": "📊 Data Analyst Agent: Querying race telemetry..."},
            {"agent": "technical_manager", "label": "🛠️ Technical Manager: Synthesizing validation trace..."},
        ],
    }
    updates: Dict[str, Any] = {"trace": trace}
    if not (state.get("answer") or "").strip():
        updates["answer"] = "No answer produced; inspect the Technical Manager trace."
    return updates
