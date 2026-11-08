"""LangGraph state machine graph compilation (P6.7)."""

import time
import uuid
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.mcp.permissions import UserContext
from app.core.tracing import telemetry
from app.core.pii_guard import pii_guard
from app.agent.nodes import (
    guardrails_node,
    intent_router_node,
    retrieval_node,
    tool_execution_node,
    synthesis_node,
    output_guard_node
)

def route_after_guardrails(state: AgentState) -> str:
    """Conditional branch after guardrail inspection."""
    if not state.is_safe:
        return "output_guard"
    return "router"

def route_by_intent(state: AgentState) -> str:
    """Conditional branch after intent classification."""
    intent = state.intent
    if intent == "knowledge_rag":
        return "retrieval"
    elif intent == "mcp_tool":
        return "tool_exec"
    elif intent == "hybrid":
        return "retrieval"
    elif intent == "blocked_security":
        return "output_guard"
    return "synthesis"

def route_after_retrieval(state: AgentState) -> str:
    """Conditional branch after retrieval: checks if hybrid requires tool execution."""
    if state.intent == "hybrid":
        return "tool_exec"
    return "synthesis"

def build_agent_graph():
    """Builds and compiles the enterprise RAG agent graph."""
    builder = StateGraph(AgentState)

    # 1. Register nodes
    builder.add_node("guardrails", guardrails_node)
    builder.add_node("router", intent_router_node)
    builder.add_node("retrieval", retrieval_node)
    builder.add_node("tool_exec", tool_execution_node)
    builder.add_node("synthesis", synthesis_node)
    builder.add_node("output_guard", output_guard_node)

    # 2. Set entry point
    builder.set_entry_point("guardrails")

    # 3. Add conditional edges
    builder.add_conditional_edges(
        "guardrails",
        route_after_guardrails,
        {
            "output_guard": "output_guard",
            "router": "router"
        }
    )

    builder.add_conditional_edges(
        "router",
        route_by_intent,
        {
            "retrieval": "retrieval",
            "tool_exec": "tool_exec",
            "synthesis": "synthesis",
            "output_guard": "output_guard"
        }
    )

    builder.add_conditional_edges(
        "retrieval",
        route_after_retrieval,
        {
            "tool_exec": "tool_exec",
            "synthesis": "synthesis"
        }
    )

    builder.add_edge("tool_exec", "synthesis")
    builder.add_edge("synthesis", "output_guard")
    builder.add_edge("output_guard", END)

    return builder.compile()

# Global compiled graph
agent_executor = build_agent_graph()

def run_agent_query(
    query: str,
    user: Optional[UserContext] = None,
    session_id: Optional[str] = None,
    target_language: Optional[str] = None
) -> AgentState:
    """Convenience function to execute an end-to-end agent query."""
    user_ctx = user or UserContext.public_default()
    trace = telemetry.start_trace(user_id=user_ctx.username, query=query, session_id=session_id)
    
    start_time = time.time()
    initial_state = AgentState(
        trace_id=trace.trace_id,
        user_context=user_ctx,
        original_query=query, target_language=target_language
    )

    try:
        result_dict = agent_executor.invoke(initial_state, config={"recursion_limit": 8})
        final_state = AgentState(**result_dict)
        final_state.latency_ms = round((time.time() - start_time) * 1000, 2)
        return final_state
    finally:
        pii_guard.cleanup_session(trace.trace_id)
        telemetry.end_trace(trace.trace_id)
