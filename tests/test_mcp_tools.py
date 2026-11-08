"""Tests for PostgreSQL-backed MCP tools and permission boundaries (P6.5 & P6.6)."""

import json
import pytest
from app.db.seed_data import seed_database
from app.mcp.server import mcp_server
from app.mcp.permissions import UserContext

@pytest.fixture(autouse=True)
def init_data():
    seed_database()

def test_mcp_tool_list_permissions():
    public_user = UserContext.public_default()
    compliance_officer = UserContext(username="alice", role="compliance_officer", department="legal", clearance_level=4)

    pub_tools = mcp_server.list_tools(user=public_user)
    pub_names = [t.name for t in pub_tools]
    assert "search_eu_ai_act_provisions" in pub_names
    assert "query_ai_system_compliance" in pub_names
    assert "submit_compliance_audit_record" not in pub_names
    assert "get_system_incident_history" not in pub_names

    comp_tools = mcp_server.list_tools(user=compliance_officer)
    comp_names = [t.name for t in comp_tools]
    assert "submit_compliance_audit_record" in comp_names
    assert "get_system_incident_history" in comp_names

def test_query_ai_system_compliance_authorized():
    officer = UserContext(username="alice", role="compliance_officer", department="legal", clearance_level=4)
    res = mcp_server.call_tool("query_ai_system_compliance", {"system_id": "SYS-HR-001"}, user=officer)
    assert not res.isError
    data = json.loads(res.content[0].text)
    assert data["system_id"] == "SYS-HR-001"
    assert data["risk_category"] == "high_risk"

def test_tool_permission_denied_incident_history():
    public_user = UserContext.public_default()
    res = mcp_server.call_tool("get_system_incident_history", {"system_id": "SYS-BIO-002"}, user=public_user)
    assert res.isError
    assert "SECURITY VIOLATION" in res.content[0].text

def test_tool_permission_denied_audit_submission():
    dev_user = UserContext(username="charlie", role="developer", department="engineering", clearance_level=2)
    res = mcp_server.call_tool(
        "submit_compliance_audit_record",
        {"system_id": "SYS-HR-001", "findings": "Pass", "compliance_status": "compliant", "risk_score": 9.0},
        user=dev_user
    )
    assert res.isError
    assert "SECURITY VIOLATION" in res.content[0].text

