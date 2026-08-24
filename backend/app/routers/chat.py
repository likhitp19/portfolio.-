import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage

from app.agents.graph import compiled_graph
from app.schemas.chat import AgentTrace, ChatRequest, ChatResponse, ChatSnapshot
from app.services.chat_layers import split_answer_layers
from app.store import get_thread, save_thread

router = APIRouter(prefix="/api")


def _serialize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    messages: List[Dict[str, Any]] = []
    for msg in state.get("messages") or []:
        content = getattr(msg, "content", msg)
        messages.append({"type": getattr(msg, "type", "unknown"), "content": content})
    return {
        "user_query": state.get("user_query"),
        "thread_id": state.get("thread_id"),
        "season_year": state.get("season_year"),
        "meeting_key": state.get("meeting_key"),
        "circuit_name": state.get("circuit_name"),
        "intent": state.get("intent"),
        "route": state.get("route"),
        "routing_rationale": state.get("routing_rationale"),
        "analysis_plan": state.get("analysis_plan") or [],
        "selected_tools": state.get("selected_tools") or [],
        "tool_calls": state.get("tool_calls") or [],
        "raw_payloads": state.get("raw_payloads") or [],
        "synthesis": state.get("synthesis") or "",
        "needs_more_data": state.get("needs_more_data"),
        "answer": state.get("answer") or "",
        "trace": state.get("trace") or {},
        "messages": messages,
    }


@router.post("/chat", response_model=ChatResponse)
async def post_chat(body: ChatRequest) -> ChatResponse:
    thread_id = body.thread_id or str(uuid.uuid4())
    initial: Dict[str, Any] = {
        "messages": [HumanMessage(content=body.message)],
        "user_query": body.message,
        "thread_id": thread_id,
        "season_year": body.year,
        "meeting_key": body.meeting_key,
        "circuit_name": None,
        "intent": "",
        "route": "",
        "routing_rationale": "",
        "analysis_plan": [],
        "selected_tools": [],
        "tool_calls": [],
        "raw_payloads": [],
        "synthesis": "",
        "needs_more_data": False,
        "answer": "",
        "trace": {},
        "analysis_notes": [],
        "missing_inputs": [],
        "assumptions": [],
    }
    result = await compiled_graph.ainvoke(initial)
    answer = result.get("answer") or ""
    layers = split_answer_layers(answer)
    trace = AgentTrace.model_validate(result.get("trace") or {})
    snapshot = ChatSnapshot(
        thread_id=thread_id,
        answer=answer,
        layers=layers,
        trace=trace,
        state=_serialize_state(result),
        route=result.get("route") or "",
    )
    save_thread(thread_id, snapshot.model_dump())
    return ChatResponse(thread_id=thread_id, answer=snapshot.answer, layers=layers, trace=trace)


@router.get("/chat/{thread_id}", response_model=ChatSnapshot)
def get_chat(thread_id: str) -> ChatSnapshot:
    snapshot = get_thread(thread_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Unknown thread_id")
    return ChatSnapshot.model_validate(snapshot)
