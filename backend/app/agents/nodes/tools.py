from typing import Any, Dict, List

from app.agents.state import F1DashboardState
from app.agents.tools import execute_tool


async def tools_node(state: F1DashboardState) -> Dict[str, Any]:
    selected = state.get("selected_tools") or []
    calls: List[Dict[str, Any]] = []
    payloads: List[Dict[str, Any]] = []
    for spec in selected:
        result = await execute_tool(spec.get("tool"), spec.get("args") or {})
        calls.append(
            {
                "tool": result["tool"],
                "args": result["args"],
                "method": result["method"],
                "path": result["path"],
                "params": result["params"],
                "status": result["status"],
                "error": result.get("error"),
                "record_count": result["record_count"],
                "timestamp": result["timestamp"],
                "sandbox_fallback": bool(result.get("sandbox_fallback")),
            }
        )
        payloads.append(
            {
                "tool": result["tool"],
                "args": result["args"],
                "status": result["status"],
                "record_count": result["record_count"],
                "preview": result.get("preview") or [],
            }
        )
    return {
        "tool_calls": calls,
        "raw_payloads": payloads,
        "selected_tools": [],
    }
