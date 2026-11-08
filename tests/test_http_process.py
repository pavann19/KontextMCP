"""Launch the real server against throwaway data and send HTTP requests."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

import httpx


def test_server_startup_http_auth_and_write(tmp_path):
    root = Path(__file__).resolve().parents[1]
    for name in ("raw", "chunks"):
        shutil.copytree(root / "data" / name, tmp_path / name)
    env = {**os.environ, "DATA_DIR": str(tmp_path), "RAW_DATA_DIR": str(tmp_path / "raw"),
           "CHUNKS_DIR": str(tmp_path / "chunks"), "QDRANT_STORAGE_DIR": str(tmp_path / "vectors"),
           "AUDIT_LOG_PATH": str(tmp_path / "audit.jsonl"),
           "DATABASE_URL": "sqlite:///" + (tmp_path / "records.db").as_posix(),
           "LANGFUSE_ENABLED": "false", "QDRANT_PREFER_LOCAL": "true", "ENVIRONMENT": "test",
           "API_KEYS": json.dumps({"http-test-credential": {"username": "http-officer", "role": "compliance_officer", "department": "legal"}})}
    seeded = subprocess.run([sys.executable, "-m", "app.db.seed_data"], cwd=root, env=env,
                            capture_output=True, text=True, timeout=30)
    assert seeded.returncode == 0, seeded.stderr
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with (tmp_path / "server-output.txt").open("w", encoding="utf-8") as log:
        process = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1", "--port", str(port)], cwd=root, env=env,
            stdout=log, stderr=subprocess.STDOUT)
        try:
            with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=5, trust_env=False) as client:
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    try:
                        if client.get("/health").status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    assert process.poll() is None, "Server exited during startup"
                    time.sleep(.1)
                else:
                    raise AssertionError("Server did not become ready")
                assert client.get("/api/v1/tools/list", headers={"X-User-Role": "admin"}).status_code == 401
                assert client.get("/api/v1/tools/list", headers={"X-API-Key": "key_alice_compliance"}).status_code == 401
                args = {"system_id": "SYS-HR-001", "findings": "Reviewed test evidence",
                        "compliance_status": "conditional_pass", "risk_score": 4.5}
                headers = {"X-API-Key": "http-test-credential"}
                bad = client.post("/api/v1/tools/call", headers=headers,
                    json={"name": "submit_compliance_audit_record", "arguments": {**args, "risk_score": True}})
                assert bad.status_code == 200 and bad.json()["isError"]
                good = client.post("/api/v1/tools/call", headers=headers,
                    json={"name": "submit_compliance_audit_record", "arguments": args})
                assert good.status_code == 200 and not good.json()["isError"], good.text
                read = client.post("/api/v1/tools/call", headers=headers,
                    json={"name": "query_ai_system_compliance", "arguments": {"system_id": "SYS-HR-001"}})
                data = json.loads(read.json()["content"][0]["text"])
                assert data["conformity_status"] == "under_assessment"
                assert any(a["findings"] == args["findings"] for a in data["assessments"])
                sdk=Path(os.environ.get("MCP_SDK_PYTHON",str(root/".venv-mcp-sdk"/("Scripts/python.exe" if os.name=="nt" else "bin/python"))))
                if sdk.is_file():
                    checked=subprocess.run([str(sdk),str(root/"scripts/check_mcp_http_sdk.py"),"--url",f"http://127.0.0.1:{port}/mcp"],env={**env,"KONTEXT_HTTP_TEST_KEY":"http-test-credential"},capture_output=True,text=True,timeout=65)
                    assert checked.returncode==0,checked.stderr
                    assert json.loads(checked.stdout)["status"]=="PASS"

        finally:
            if os.name == "nt":
                # Windows virtualenv launchers can own a separate Python child.
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               capture_output=True, timeout=15)
            else:
                process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
