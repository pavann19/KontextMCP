"""MCP Protocol standard compliance and JSON-RPC 2.0 lifecycle tests (P1 - Section 6.1)."""

import pytest
import json
from app.mcp.server import mcp_server
from app.mcp.permissions import UserContext

@pytest.fixture
def compliance_user():
    return UserContext(username="alice_compliance", role="compliance_officer", department="legal_compliance", clearance_level=4)

@pytest.fixture
def public_user():
    return UserContext(username="eva_public", role="public_viewer", department="public", clearance_level=1)

def test_mcp_initialize_lifecycle():
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        }
    }
    resp = mcp_server.handle_jsonrpc(req)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    assert "result" in resp
    res = resp["result"]
    assert res["protocolVersion"] == "2024-11-05"
    assert res["serverInfo"]["name"] == "kontext-mcp"
    assert "tools" in res["capabilities"]

def test_mcp_ping():
    req = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
    resp = mcp_server.handle_jsonrpc(req)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 2
    assert resp["result"] == {}

def test_mcp_tools_list_role_filtering(public_user, compliance_user):
    # 1. Public user listing tools
    req_pub = {"jsonrpc": "2.0", "id": 3, "method": "tools/list"}
    resp_pub = mcp_server.handle_jsonrpc(req_pub, user=public_user)
    pub_tools = resp_pub["result"]["tools"]
    pub_tool_names = [t["name"] for t in pub_tools]
    assert "search_eu_ai_act_provisions" in pub_tool_names
    assert "query_ai_system_compliance" in pub_tool_names
    # Restricted tools must be omitted
    assert "get_system_incident_history" not in pub_tool_names
    assert "submit_compliance_audit_record" not in pub_tool_names

    # 2. Compliance officer listing tools
    req_comp = {"jsonrpc": "2.0", "id": 4, "method": "tools/list"}
    resp_comp = mcp_server.handle_jsonrpc(req_comp, user=compliance_user)
    comp_tools = resp_comp["result"]["tools"]
    comp_tool_names = [t["name"] for t in comp_tools]
    assert len(comp_tools) == 5  # Has access to all 5 tools
    assert "submit_compliance_audit_record" in comp_tool_names

def test_mcp_tools_call_success(compliance_user):
    req = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "query_ai_system_compliance",
            "arguments": {"system_id": "SYS-HR-001"}
        }
    }
    resp = mcp_server.handle_jsonrpc(req, user=compliance_user)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 5
    assert "result" in resp
    content = resp["result"]["content"]
    assert len(content) > 0
    assert "SYS-HR-001" in content[0]["text"]

def test_mcp_tools_call_permission_denied_returns_jsonrpc_error(public_user):
    req = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "get_system_incident_history",
            "arguments": {"system_id": "SYS-HR-001"}
        }
    }
    resp = mcp_server.handle_jsonrpc(req, user=public_user)
    assert resp["jsonrpc"] == "2.0"
    assert "error" in resp
    assert resp["error"]["code"] == -32001
    assert "SECURITY VIOLATION" in resp["error"]["message"]

def test_mcp_schema_validation_missing_required_parameter(compliance_user):
    req = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {
            "name": "query_ai_system_compliance",
            "arguments": {}  # Missing 'system_id'
        }
    }
    resp = mcp_server.handle_jsonrpc(req, user=compliance_user)
    assert "error" in resp
    assert resp["error"]["code"] == -32602
    assert "Missing required parameter 'system_id'" in resp["error"]["message"]

def test_mcp_unknown_method_error():
    req = {"jsonrpc": "2.0", "id": 8, "method": "non_existent_method"}
    resp = mcp_server.handle_jsonrpc(req)
    assert "error" in resp
    assert resp["error"]["code"] == -32601
    assert "Method not found" in resp["error"]["message"]

