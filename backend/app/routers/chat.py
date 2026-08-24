import json
import re
import uuid
from typing import Any, AsyncIterator, Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.agents.graph import compiled_graph
from app.schemas.chat import AgentTrace, ChatLayers, ChatRequest, ChatResponse, ChatSnapshot
from app.services.chat_layers import split_answer_layers
from app.store import get_thread, save_thread

router = APIRouter(prefix="/api")

HANDOFF_BY_NODE = {
    "generalist": {
        "agent": "generalist",
        "label": "🤖 Generalist Orchestrator: Planning query...",
    },
    "data_analyst": {
        "agent": "data_analyst",
        "label": "📊 Data Analyst Agent: Querying race telemetry...",
    },
    "tools": {
        "agent": "data_analyst",
        "label": "📊 Data Analyst Agent: Querying race telemetry...",
    },
    "researcher": {
        "agent": "data_analyst",
        "label": "📊 Data Analyst Agent: Querying race telemetry...",
    },
    "strategic_analyst": {
        "agent": "strategic_analyst",
        "label": "📈 Strategic Analyst: Evaluating pace, reliability, and margins...",
    },
    "technical_manager": {
        "agent": "technical_manager",
        "label": "🛠️ Technical Manager: Synthesizing validation trace...",
    },
}


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
        "report_meta": state.get("report_meta") or {},
        "messages": messages,
    }


def _initial_state(body: ChatRequest, thread_id: str) -> Dict[str, Any]:
    return {
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
        "report_meta": {},
        "analysis_notes": [],
        "missing_inputs": [],
        "assumptions": [],
    }


def _layers_from_result(result: Dict[str, Any]) -> ChatLayers:
    answer = result.get("answer") or ""
    layers = split_answer_layers(answer)
    meta = result.get("report_meta") or {}
    if meta.get("predicted_winner"):
        layers.predicted_winner = str(meta["predicted_winner"])
    if meta.get("confidence") is not None:
        layers.confidence = float(meta["confidence"])
    if meta.get("key_drivers"):
        layers.key_drivers = [str(item) for item in meta["key_drivers"]]
    if meta.get("contenders"):
        layers.contenders = meta["contenders"]
    if meta.get("follow_ups"):
        layers.follow_ups = [str(item) for item in meta["follow_ups"]]
    return layers


def _snapshot(thread_id: str, result: Dict[str, Any]) -> ChatSnapshot:
    answer = result.get("answer") or ""
    layers = _layers_from_result(result)
    trace = AgentTrace.model_validate(result.get("trace") or {})
    return ChatSnapshot(
        thread_id=thread_id,
        answer=answer,
        layers=layers,
        trace=trace,
        state=_serialize_state(result),
        route=result.get("route") or "",
    )


@router.post("/chat", response_model=ChatResponse)
async def post_chat(body: ChatRequest) -> ChatResponse:
    thread_id = body.thread_id or str(uuid.uuid4())
    result = await compiled_graph.ainvoke(_initial_state(body, thread_id))
    snapshot = _snapshot(thread_id, result)
    save_thread(thread_id, snapshot.model_dump())
    return ChatResponse(thread_id=thread_id, answer=snapshot.answer, layers=snapshot.layers, trace=snapshot.trace)


def _sse(event: str, payload: Dict[str, Any]) -> str:
    return "event: {0}\ndata: {1}\n\n".format(event, json.dumps(payload, default=str))


@router.post("/chat/stream")
async def stream_chat(body: ChatRequest) -> StreamingResponse:
    thread_id = body.thread_id or str(uuid.uuid4())
    initial = _initial_state(body, thread_id)

    async def events() -> AsyncIterator[str]:
        result: Dict[str, Any] = {}
        try:
            async for mode, chunk in compiled_graph.astream(initial, stream_mode=["updates", "values"]):
                if mode == "updates" and isinstance(chunk, dict):
                    for node in chunk:
                        handoff = HANDOFF_BY_NODE.get(str(node))
                        if handoff:
                            yield _sse("handoff", handoff)
                elif mode == "values" and isinstance(chunk, dict):
                    result = chunk
        except TypeError:
            result = await compiled_graph.ainvoke(initial)
            for node in ("generalist", "data_analyst", "strategic_analyst", "technical_manager"):
                yield _sse("handoff", HANDOFF_BY_NODE[node])
        snapshot = _snapshot(thread_id, result)
        save_thread(thread_id, snapshot.model_dump())
        yield _sse(
            "result",
            ChatResponse(
                thread_id=thread_id,
                answer=snapshot.answer,
                layers=snapshot.layers,
                trace=snapshot.trace,
            ).model_dump(),
        )

    return StreamingResponse(events(), media_type="text/event-stream")


@router.get("/chat/{thread_id}", response_model=ChatSnapshot)
def get_chat(thread_id: str) -> ChatSnapshot:
    snapshot = get_thread(thread_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Unknown thread_id")
    return ChatSnapshot.model_validate(snapshot)
