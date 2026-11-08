"""Exercise the actual process transport, not just Python dispatcher methods."""
import json
import os
from pathlib import Path
import subprocess
import sys


def test_stdio_initialize_list_read_and_notification():
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize"},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "query_ai_system_compliance", "arguments": {"system_id": "SYS-CHAT-004"}}},
    ]
    result = subprocess.run([sys.executable, "-m", "scripts.start_mcp"],
        cwd=Path(__file__).resolve().parents[2], env={**os.environ, "MCP_API_KEY": ""},
        input="\n".join(json.dumps(m) for m in messages)+"\nnot-json\n",
        capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    responses = [json.loads(line) for line in result.stdout.splitlines()]
    assert [r["id"] for r in responses] == [1, 2, 3, None]
    assert responses[0]["result"]["protocolVersion"] == "2024-11-05"
    assert {t["name"] for t in responses[1]["result"]["tools"]} == {
        "query_ai_system_compliance", "search_eu_ai_act_provisions"}
    assert not responses[2]["result"]["isError"]
    assert responses[3]["error"]["code"] == -32700


def test_malformed_tool_arguments_fail_without_dispatch():
    from app.mcp.server import mcp_server
    for name, arguments in [([], {}), ("query_ai_system_compliance", []),
                             ("search_eu_ai_act_provisions", {"query": "Article 5", "top_k": True})]:
        result = mcp_server.call_tool(name, arguments)
        assert result.isError
    response = mcp_server.handle_jsonrpc({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": [], "arguments": {}}})
    assert response["error"]["code"] == -32602
