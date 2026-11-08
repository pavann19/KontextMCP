"""Tests for direct DB access, indirect MCP tool calls, and cross-department permissions.

Verifies:
1. Direct database access row-level filtering vs indirect MCP tool calls.
2. Cross-department access boundaries using different employee identities.
"""

import json
import pytest
from app.db.session import get_db_context
from app.db.models import AISystem, IncidentReport, ComplianceAssessment
from app.mcp.permissions import UserContext, PermissionManager
from app.mcp.server import mcp_server
from app.agent.graph import run_agent_query

@pytest.fixture(scope="module")
def identities():
    return {
        "david_hr_dev": UserContext(username="david_hr_dev", role="developer", department="human_resources", clearance_level=2),
        "charlie_eng_dev": UserContext(username="charlie_dev", role="developer", department="engineering", clearance_level=2),
        "bob_auditor": UserContext(username="bob_auditor", role="auditor", department="internal_audit", clearance_level=3),
        "alice_compliance": UserContext(username="alice_compliance", role="compliance_officer", department="legal_compliance", clearance_level=4),
        "eva_public": UserContext(username="eva_public", role="public_viewer", department="public", clearance_level=1)
    }

def test_direct_db_row_level_boundaries(identities):
    """Verifies that direct database query logic applies row-level ABAC filters."""
    with get_db_context() as session:
        systems = session.query(AISystem).all()
        hr_sys = next(s for s in systems if s.system_id == "SYS-HR-001")
        bio_sys = next(s for s in systems if s.system_id == "SYS-BIO-002")
        public_sys = next(s for s in systems if s.system_id == "SYS-CHAT-004")

        # 1. David (HR Developer) directly checking access rules
        assert PermissionManager.can_access_system_record(hr_sys.department, hr_sys.is_public_registry, identities["david_hr_dev"]) is True
        assert PermissionManager.can_access_system_record(bio_sys.department, bio_sys.is_public_registry, identities["david_hr_dev"]) is False
        assert PermissionManager.can_access_system_record(public_sys.department, public_sys.is_public_registry, identities["david_hr_dev"]) is True

        # 2. Charlie (Engineering Developer) checking access rules
        assert PermissionManager.can_access_system_record(hr_sys.department, hr_sys.is_public_registry, identities["charlie_eng_dev"]) is False
        assert PermissionManager.can_access_system_record(bio_sys.department, bio_sys.is_public_registry, identities["charlie_eng_dev"]) is False
        assert PermissionManager.can_access_system_record(public_sys.department, public_sys.is_public_registry, identities["charlie_eng_dev"]) is True

        # 3. Bob (Auditor) enterprise-wide access
        assert PermissionManager.can_access_system_record(hr_sys.department, hr_sys.is_public_registry, identities["bob_auditor"]) is True
        assert PermissionManager.can_access_system_record(bio_sys.department, bio_sys.is_public_registry, identities["bob_auditor"]) is True

        # 4. Eva (Public Viewer) only public systems
        assert PermissionManager.can_access_system_record(hr_sys.department, hr_sys.is_public_registry, identities["eva_public"]) is False
        assert PermissionManager.can_access_system_record(public_sys.department, public_sys.is_public_registry, identities["eva_public"]) is True

def test_cross_department_indirect_mcp_tool_calls(identities):
    """Tests cross-department access via MCP tool executions."""
    # David queries his own department's HR system -> ALLOWED
    res_hr = mcp_server.call_tool("query_ai_system_compliance", {"system_id": "SYS-HR-001"}, user=identities["david_hr_dev"])
    assert not res_hr.isError
    data_hr = json.loads(res_hr.content[0].text)
    assert data_hr["system_id"] == "SYS-HR-001"
    assert data_hr["department"] == "human_resources"

    # David attempts to query Security Operations system (SYS-BIO-002) -> DENIED (Cross-dept violation)
    res_cross = mcp_server.call_tool("query_ai_system_compliance", {"system_id": "SYS-BIO-002"}, user=identities["david_hr_dev"])
    assert res_cross.isError
    assert "ROW-LEVEL PERMISSION DENIED" in res_cross.content[0].text
    assert "security" not in res_cross.content[0].text.lower()  # Do not disclose target department.

    # Charlie (Engineering) attempts to query HR system -> DENIED (Cross-dept violation)
    res_charlie = mcp_server.call_tool("query_ai_system_compliance", {"system_id": "SYS-HR-001"}, user=identities["charlie_eng_dev"])
    assert res_charlie.isError
    assert "ROW-LEVEL PERMISSION DENIED" in res_charlie.content[0].text

    # Both Charlie and David can query the public customer chatbot -> ALLOWED
    res_pub_c = mcp_server.call_tool("query_ai_system_compliance", {"system_id": "SYS-CHAT-004"}, user=identities["charlie_eng_dev"])
    assert not res_pub_c.isError
    assert json.loads(res_pub_c.content[0].text)["is_public_registry"] is True

def test_agent_indirect_tool_routing_enforces_boundaries(identities):
    """Tests that indirect tool calls dispatched through the LangGraph agent enforce boundaries."""
    # 1. Developer asks agent for another department's system
    state_dev = run_agent_query("What is the compliance status of system SYS-BIO-002?", identities["david_hr_dev"])
    assert "ROW-LEVEL PERMISSION DENIED" in state_dev.final_answer or "Alert / Error" in state_dev.final_answer

    # 2. Compliance officer asks agent for same system -> ALLOWED
    state_comp = run_agent_query("What is the compliance status of system SYS-BIO-002?", identities["alice_compliance"])
    assert "BioGate Remote Biometric ID" in state_comp.final_answer
    assert "under_assessment" in state_comp.final_answer

    # 3. Developer attempts incident lookup via agent -> DENIED
    state_inc = run_agent_query("Show me incident reports for SYS-HR-001", identities["david_hr_dev"])
    assert "SECURITY VIOLATION" in state_inc.final_answer or "Alert / Error" in state_inc.final_answer

    # 4. Auditor attempts incident lookup via agent -> ALLOWED
    state_auditor = run_agent_query("Show me incident reports for SYS-HR-001", identities["bob_auditor"])
    assert "INC-2026-002" in state_auditor.final_answer or "fundamental_rights_breach" in state_auditor.final_answer

