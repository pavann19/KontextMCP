"""Interoperate with the SDK in a separate Python environment and subprocess."""
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest


def test_official_sdk_stdio_read_deny_and_write():
    root = Path(__file__).resolve().parents[2]
    default = root / ".venv-mcp-sdk" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    interpreter = Path(os.environ.get("MCP_SDK_PYTHON", str(default)))
    if not interpreter.is_file():
        pytest.skip("Install requirements-mcp-client.txt in .venv-mcp-sdk or set MCP_SDK_PYTHON.")
    result = subprocess.run([str(interpreter), str(root / "scripts/check_mcp_sdk.py"), "--server-python", sys.executable],
        cwd=root, env={**os.environ, "KONTEXT_SDK_TEST_ISOLATED": "1"}, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=85)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["sdk_version"] == "2.3.0"
    assert data["status"] == "PASS"
    assert {c["operation"] for c in data["checks"]} == {"list_and_public_read", "protected_read_denied", "explicit_write_and_readback"}
    if os.environ.get("MCP_SDK_REPORT_PATH"):
        Path(os.environ["MCP_SDK_REPORT_PATH"]).write_text(json.dumps(data, indent=2), encoding="utf-8")
