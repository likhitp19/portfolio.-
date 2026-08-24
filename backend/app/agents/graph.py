from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.nodes.data_analyst import data_analyst_node
from app.agents.nodes.generalist import generalist_node
from app.agents.nodes.researcher import researcher_node
from app.agents.nodes.strategic_analyst import strategic_analyst_node
from app.agents.nodes.technical_manager import technical_manager_node
from app.agents.nodes.tools import tools_node
from app.agents.state import F1DashboardState

MAX_TOOL_ITERATIONS = 16


def route_after_generalist(state: F1DashboardState) -> str:
    route = state.get("route") or ""
    if route == "data_analyst":
        return "data_analyst"
    if route == "researcher":
        return "researcher"
    return "technical_manager"


def route_after_analyst(state: F1DashboardState) -> str:
    tool_calls = state.get("tool_calls") or []
    if state.get("needs_more_data") and len(tool_calls) < MAX_TOOL_ITERATIONS:
        return "tools"
    if (state.get("intent") or "") == "championship_projection" and (state.get("route") or "") == "data_analyst":
        return "strategic_analyst"
    return "technical_manager"


def route_after_tools(state: F1DashboardState) -> str:
    if state.get("route") == "researcher":
        return "researcher"
    return "data_analyst"


def build_graph():
    graph = StateGraph(F1DashboardState)
    graph.add_node("generalist", generalist_node)
    graph.add_node("data_analyst", data_analyst_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("tools", tools_node)
    graph.add_node("strategic_analyst", strategic_analyst_node)
    graph.add_node("technical_manager", technical_manager_node)
    graph.add_edge(START, "generalist")
    graph.add_conditional_edges(
        "generalist",
        route_after_generalist,
        {
            "data_analyst": "data_analyst",
            "researcher": "researcher",
            "technical_manager": "technical_manager",
        },
    )
    graph.add_conditional_edges(
        "data_analyst",
        route_after_analyst,
        {"tools": "tools", "strategic_analyst": "strategic_analyst", "technical_manager": "technical_manager"},
    )
    graph.add_conditional_edges(
        "researcher",
        route_after_analyst,
        {"tools": "tools", "strategic_analyst": "strategic_analyst", "technical_manager": "technical_manager"},
    )
    graph.add_edge("strategic_analyst", "technical_manager")
    graph.add_conditional_edges(
        "tools",
        route_after_tools,
        {"data_analyst": "data_analyst", "researcher": "researcher"},
    )
    graph.add_edge("technical_manager", END)
    return graph.compile()


compiled_graph = build_graph()
