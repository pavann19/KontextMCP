"""Tests for FastAPI API endpoints."""

import pytest
from app.mcp.permissions import UserContext
from app.api.routes_chat import chat_endpoint, ChatRequest
from app.api.routes_search import search_provisions
from app.api.routes_tools import list_authorized_tools, execute_tool, CallToolRequest
from app.api.routes_audit import verify_audit_integrity, get_audit_logs

def test_api_chat_endpoint():
    user = UserContext(username="alice", role="compliance_officer", department="legal", clearance_level=4)
    req = ChatRequest(query="What are the transparency rules under Article 50?")
    resp = chat_endpoint(request=req, user=user)

    assert resp.trace_id
    assert resp.is_safe
    assert len(resp.answer) > 50
    assert any("50" in c["article_id"] for c in resp.citations)

def test_api_search_endpoint():
    user = UserContext.public_default()
    resp = search_provisions(q="Article 5 prohibited practices", method="reranked", top_k=2, user=user)

    assert resp.total_returned == 2
    assert "Article 5" in resp.hits[0].article_id

def test_api_tools_list_endpoint():
    user = UserContext.public_default()
    tools = list_authorized_tools(user=user)
    assert len(tools) >= 2
    names = [t.name for t in tools]
    assert "submit_compliance_audit_record" not in names

def test_api_audit_verify_endpoint():
    user = UserContext(username="alice", role="compliance_officer", department="legal", clearance_level=4)
    res = verify_audit_integrity(user=user)
    assert res.is_valid
    assert res.verification_status == "CRYPTOGRAPHIC_CHAIN_VERIFIED"

