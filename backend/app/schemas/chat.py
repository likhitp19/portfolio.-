from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class DriverContender(BaseModel):
    driver_number: str = ""
    full_name: str = ""
    team_name: str = ""
    points: float = 0
    position: int = 0
    headshot_url: Optional[str] = None


class ChatLayers(BaseModel):
    executive_summary: str = ""
    deep_dive: str = ""
    predicted_winner: Optional[str] = None
    confidence: Optional[float] = None
    key_drivers: List[str] = Field(default_factory=list)
    contenders: List[DriverContender] = Field(default_factory=list)
    follow_ups: List[str] = Field(default_factory=list)


class AgentTrace(BaseModel):
    routing: Dict[str, Any] = Field(default_factory=dict)
    reasoning_path: List[Dict[str, Any]] = Field(default_factory=list)
    api_calls: List[Dict[str, Any]] = Field(default_factory=list)
    pipelines: List[Dict[str, Any]] = Field(default_factory=list)
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list)
    missing_inputs: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    finance_cards: List[Dict[str, Any]] = Field(default_factory=list)
    agent_handoffs: List[Dict[str, Any]] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    year: Optional[int] = None
    meeting_key: Optional[int] = None


class ChatResponse(BaseModel):
    thread_id: str
    answer: str
    layers: ChatLayers = Field(default_factory=ChatLayers)
    trace: AgentTrace


class ChatSnapshot(BaseModel):
    thread_id: str
    answer: str
    layers: ChatLayers = Field(default_factory=ChatLayers)
    trace: AgentTrace
    state: Dict[str, Any]
    route: Union[str] = ""
