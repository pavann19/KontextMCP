"""Chat and conversational agent API routes (P6.7 & P6.10)."""

from typing import Optional, Dict, Any, List, Literal
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from app.core.security import resolve_user_context
from app.mcp.permissions import UserContext
from app.agent.graph import run_agent_query

router = APIRouter(prefix="/chat", tags=["Agentic Chat"])

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=16000, description="The user query in German or English.")
    session_id: Optional[str] = Field(None, description="Optional conversational session ID.")
    target_language: Optional[Literal["en", "de"]] = Field(None, description="Explicit language preference ('en' or 'de').")

class ChatResponse(BaseModel):
    trace_id: str
    user: str
    role: str
    query: str
    sanitized_query: str
    intent: str
    is_safe: bool
    has_pii: bool
    pii_entities_detected: int
    synthesis_backend: str
    grounding_status: str
    grounding_error: Optional[str] = None
    answer: str
    citations: List[Dict[str, str]]
    tool_results: List[Dict[str, Any]]
    latency_ms: float

@router.post("", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest,
    user: UserContext = Depends(resolve_user_context)
):
    """Executes an agent query through LangGraph with full guardrails and tool integration."""
    state = run_agent_query(
        query=request.query,
        user=user,
        session_id=request.session_id,
        target_language=request.target_language
    )

    return ChatResponse(
        trace_id=state.trace_id,
        user=user.username,
        role=user.role,
        query=state.original_query,
        sanitized_query=state.sanitized_query,
        intent=state.intent,
        is_safe=state.is_safe,
        has_pii=state.has_pii,
        pii_entities_detected=state.pii_entity_count,
        answer=state.final_answer,
        grounding_status=state.grounding_status,
        synthesis_backend=state.synthesis_backend,
        grounding_error=state.grounding_error,
        citations=state.citations,
        tool_results=state.tool_results,
        latency_ms=state.latency_ms
    )

