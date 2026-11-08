"""Exhaustive cross-department isolation and clearance tests (P0 - Section 4.2)."""

import pytest
import json
from app.mcp.permissions import UserContext, PermissionManager
from app.mcp.server import mcp_server

@pytest.fixture(scope="module")
def dept_users():
    return {
        "hr_dev": UserContext(username="david_hr_dev", role="developer", department="human_resources", clearance_level=2),
        "eng_dev": UserContext(username="charlie_dev", role="developer", department="engineering", clearance_level=2),
        "auditor": UserContext(username="bob_auditor", role="auditor", department="internal_audit", clearance_level=3),
        "compliance": UserContext(username="alice_compliance", role="compliance_officer", department="legal_compliance", clearance_level=4),
        "public": UserContext(username="eva_public", role="public_viewer", department="public", clearance_level=1)
    }

def test_hr_developer_cannot_view_engineering_systems(dept_users):
    res = mcp_server.call_tool("query_ai_system_compliance", {"system_id": "SYS-FIN-001"}, user=dept_users["hr_dev"])
    # If SYS-FIN-001 is in finance / engineering and not public
    assert res.isError or "ROW-LEVEL PERMISSION DENIED" in res.content[0].text or "No registered" in res.content[0].text

def test_engineering_developer_cannot_view_hr_systems(dept_users):
    res = mcp_server.call_tool("query_ai_system_compliance", {"system_id": "SYS-HR-001"}, user=dept_users["eng_dev"])
    assert res.isError
    assert "ROW-LEVEL PERMISSION DENIED" in res.content[0].text

def test_developers_restricted_in_high_risk_list(dept_users):
    res = mcp_server.call_tool("list_high_risk_systems", {"risk_level": "high_risk"}, user=dept_users["hr_dev"])
    assert not res.isError
    data = json.loads(res.content[0].text)
    for s in data["systems"]:
        # Must either be in HR or public
        assert s["department"] == "human_resources" or s.get("is_public_registry", False)

def test_auditor_has_cross_department_read_access(dept_users):
    res = mcp_server.call_tool("list_high_risk_systems", {"risk_level": "high_risk"}, user=dept_users["auditor"])
    assert not res.isError
    data = json.loads(res.content[0].text)
    depts = {s["department"] for s in data["systems"]}
    assert len(depts) >= 2  # Sees across multiple departments

def test_public_user_blocked_from_all_internal_tools(dept_users):
    tools_to_block = [
        ("list_high_risk_systems", {"risk_level": "high_risk"}),
        ("get_system_incident_history", {"system_id": "SYS-HR-001"}),
        ("submit_compliance_audit_record", {
            "system_id": "SYS-HR-001",
            "findings": "test",
            "compliance_status": "compliant",
            "risk_score": 5.0
        })
    ]
    for tool_name, args in tools_to_block:
        res = mcp_server.call_tool(tool_name, args, user=dept_users["public"])
        assert res.isError
        assert ("SECURITY VIOLATION" in res.content[0].text or "Insufficient clearance" in res.content[0].text)

