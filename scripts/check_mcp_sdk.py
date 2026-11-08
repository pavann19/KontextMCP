"""Independent SDK client check. Run under the separately installed SDK interpreter.

The caller must provide an isolated, seeded database via environment settings.
Only test fixtures are written. Never point this check at an application database.
"""
import argparse
import asyncio
import json
import os
from importlib.metadata import version
from pathlib import Path
from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parents[1]


async def check(server_python):
    # Explicit isolated environment is inherited from pytest, not from the SDK's
    # minimal subprocess allow-list. Only application configuration is forwarded.
    keys = ("DATA_DIR", "RAW_DATA_DIR", "CHUNKS_DIR", "QDRANT_STORAGE_DIR", "AUDIT_LOG_PATH",
            "DATABASE_URL", "AUDIT_CHECKPOINT_KEY", "QDRANT_PREFER_LOCAL", "QDRANT_HOST")
    env = {k: os.environ[k] for k in keys if k in os.environ}
    if os.environ.get("KONTEXT_SDK_TEST_ISOLATED") != "1":
        raise RuntimeError("This fixture-writing check requires KONTEXT_SDK_TEST_ISOLATED=1.")
    env.update({"ENVIRONMENT": "test", "DATABASE_SCHEMA_MODE": "create",
                "LANGFUSE_ENABLED": "false", "PYTHONPATH": str(ROOT)})
    credential = "sdk-test-fixture-credential"
    mapping = {credential: {"username": "sdk-officer", "role": "compliance_officer", "department": "legal"}}
    env["API_KEYS"] = json.dumps(mapping)
    checks = []
    for identity in ("public", "officer"):
        child_env = {**env, "MCP_API_KEY": credential if identity == "officer" else ""}
        params = StdioServerParameters(command=server_python, args=["-m", "scripts.start_mcp"], env=child_env, cwd=str(ROOT))
        async with Client(params) as client:
            listing = await client.list_tools()
            names = {tool.name for tool in listing.tools}
            assert ("submit_compliance_audit_record" in names) == (identity == "officer")
            read = await client.call_tool("query_ai_system_compliance", {"system_id": "SYS-CHAT-004"})
            assert not read.is_error
            assert json.loads(read.content[0].text)["system_id"] == "SYS-CHAT-004"
            checks.append({"identity": identity, "protocol": client.protocol_version, "operation": "list_and_public_read", "status": "PASS"})
            if identity == "public":
                try:
                    denied = await client.call_tool("get_system_incident_history", {"system_id": "SYS-HR-001"})
                except Exception as exc:
                    # The gateway represents authorization denials as JSON-RPC errors.
                    assert "SECURITY VIOLATION" in str(exc), str(exc)
                else:
                    assert denied.is_error and "SECURITY VIOLATION" in denied.content[0].text
                checks.append({"identity": identity, "operation": "protected_read_denied", "status": "PASS"})
            else:
                write = await client.call_tool("submit_compliance_audit_record", {
                    "system_id": "SYS-HR-001", "findings": "SDK test fixture evidence",
                    "compliance_status": "conditional_pass", "risk_score": 4.0})
                assert not write.is_error
                created = json.loads(write.content[0].text)
                read_back = await client.call_tool("query_ai_system_compliance", {"system_id": "SYS-HR-001"})
                assert not read_back.is_error
                record = json.loads(read_back.content[0].text)
                assert any(row["assessment_id"] == created["assessment_id"] and row["findings"] == "SDK test fixture evidence" for row in record["assessments"])
                checks.append({"identity": identity, "operation": "explicit_write_and_readback", "status": "PASS"})
    return {"status": "PASS", "client": "official Python SDK", "sdk_version": version("mcp"),
            "transport": "stdio", "checks": checks,
            "limitation": "One SDK version against local fixture storage. Desktop hosts, HTTP transport and production deployments are unverified."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-python", required=True)
    args = parser.parse_args()
    result = asyncio.run(asyncio.wait_for(check(args.server_python), timeout=60))
    print(json.dumps(result))

if __name__ == "__main__":
    main()
