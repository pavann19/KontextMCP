"""LangGraph agent failure recovery and execution limit tests (P2 - Section 11)."""

import pytest
from app.agent.graph import run_agent_query
from app.mcp.permissions import UserContext

@pytest.fixture
def compliance_user():
    return UserContext(username="alice_compliance", role="compliance_officer", department="legal_compliance", clearance_level=4)

def test_agent_graceful_recovery_on_empty_retrieval(compliance_user):
    # Query with no matching keywords or obscure tokens
    state = run_agent_query("xyzqwk123987 non-existent statutory article query", user=compliance_user)
    assert state.is_safe is True
    assert len(state.final_answer) > 0
    # Must not throw an unhandled exception or crash

def test_agent_output_guard_finalizes_audit_trace(compliance_user):
    state = run_agent_query("What are the risk management requirements in Article 9?", user=compliance_user)
    assert state.trace_id.startswith("trc-")
    assert state.latency_ms > 0.0
    assert len(state.final_answer) > 0

def test_agent_tool_error_graceful_synthesis(compliance_user):
    # Requesting a non-existent system ID
    state = run_agent_query("What is the status of system SYS-NONEXISTENT-999?", user=compliance_user)
    assert state.is_safe is True
    assert "No registered AI system found" in state.final_answer or "Alert / Error" in state.final_answer

