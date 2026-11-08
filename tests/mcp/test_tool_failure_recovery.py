"""MCP tool error handling and failure recovery tests (P1 - Section 6.2)."""

import pytest
from app.mcp.server import mcp_server
from app.mcp.permissions import UserContext
from app.db.session import get_db_context
from app.db.models import AISystem, ComplianceAssessment

@pytest.fixture
def compliance_user():
    return UserContext(username="alice_compliance", role="compliance_officer", department="legal_compliance", clearance_level=4)

def test_tool_unexpected_parameter_type(compliance_user):
    req = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {
            "name": "query_ai_system_compliance",
            "arguments": {"system_id": 12345}  # Integer instead of string
        }
    }
    resp = mcp_server.handle_jsonrpc(req, user=compliance_user)
    assert "error" in resp
    assert resp["error"]["code"] == -32602
    assert "not of type" in resp["error"]["message"]

def test_tool_empty_results_handling(compliance_user):
    res = mcp_server.call_tool("query_ai_system_compliance", {"system_id": "SYS-DOESNOTEXIST-999"}, user=compliance_user)
    assert res.isError
    assert "No registered AI system found" in res.content[0].text

def test_write_operation_rolls_back_on_invalid_status(compliance_user):
    # Attempting to submit audit record with invalid compliance_status
    with get_db_context() as session:
        initial_count = session.query(ComplianceAssessment).count()

    res = mcp_server.call_tool(
        "submit_compliance_audit_record",
        {
            "system_id": "SYS-HR-001",
            "findings": "Test failure rollback",
            "compliance_status": "INVALID_STATUS_VALUE",
            "risk_score": 5.0
        },
        user=compliance_user
    )
    assert res.isError
    assert "Schema validation error" in res.content[0].text

    # Verify transaction did not commit
    with get_db_context() as session:
        new_count = session.query(ComplianceAssessment).count()
        assert new_count == initial_count

def test_read_only_tool_does_not_mutate_system(compliance_user):
    with get_db_context() as session:
        sys_before = session.query(AISystem).filter(AISystem.system_id == "SYS-HR-001").first()
        status_before = sys_before.conformity_status
        audit_date_before = sys_before.last_audit_date

    # Read-only query
    res = mcp_server.call_tool("query_ai_system_compliance", {"system_id": "SYS-HR-001"}, user=compliance_user)
    assert not res.isError

    with get_db_context() as session:
        sys_after = session.query(AISystem).filter(AISystem.system_id == "SYS-HR-001").first()
        assert sys_after.conformity_status == status_before
        assert sys_after.last_audit_date == audit_date_before

