"""LangGraph Agent State Definitions (P6.7)."""

from typing import List, Dict, Any, Optional, Annotated
from pydantic import BaseModel, Field
from app.mcp.permissions import UserContext

class AgentState(BaseModel):
    """Execution state passed through the LangGraph nodes."""
    # Identification & Auth
    trace_id: str
    user_context: UserContext = Field(default_factory=UserContext.public_default)
    
    # Ingress Query & Guardrail State
    original_query: str
    sanitized_query: str = ""
    target_language: Optional[str] = None  # en or de
    has_pii: bool = False
    pii_entity_count: int = 0
    is_safe: bool = True
    security_flag: Optional[str] = None
    
    # Routing & Intent
    intent: str = "direct_chat"  # knowledge_rag, mcp_tool, hybrid, direct_chat, blocked_security
    
    # Retrieval
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Tool Execution
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    tool_errors: List[str] = Field(default_factory=list)
    
    # Egress / Synthesis
    synthesis_backend: str = "extractive"
    answer_mode: str = "notice"
    grounding_status: str = "NOT_APPLICABLE"
    grounding_error: Optional[str] = None
    final_answer: str = ""
    citations: List[Dict[str, str]] = Field(default_factory=list)
    latency_ms: float = 0.0
    evaluation_scores: Dict[str, float] = Field(default_factory=dict)

