"""Validate the existing Docker deployment using disposable project-scoped storage."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import sys
import time
import uuid
import xml.etree.ElementTree as ET

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.process_runner import run_bounded


def source_fingerprint():
    digest = hashlib.sha256()
    files = [*ROOT.glob("app/**/*.py"), *ROOT.glob("tests/**/*.py"), *ROOT.glob("scripts/*.py"),
             *ROOT.glob("docker/*"), *ROOT.glob("requirements*.txt"),
             *ROOT.glob("requirements*.lock"), *ROOT.glob("migrations/**/*.py"),
             *ROOT.glob(".github/workflows/*"), ROOT/".dockerignore"]
    for path in sorted(p for p in files if p.is_file()):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def main():
    project = "kontext-validation-" + uuid.uuid4().hex[:10]
    output = ROOT / "artifacts" / "docker" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output.mkdir(parents=True)
    free_bytes = shutil.disk_usage(ROOT).free
    if free_bytes < 2 * 1024**3:
        report = {"status": "BLOCKED_STORAGE", "free_bytes": free_bytes,
                  "minimum_free_bytes": 2 * 1024**3,
                  "reason": "Insufficient workspace storage for an isolated image build; no resources started.",
                  "timestamp": datetime.now(timezone.utc).isoformat(), "cleanup": "NOT_REQUIRED"}
        (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"BLOCKED_STORAGE: {output / 'report.json'}", flush=True)
        return 1
    preflight = run_bounded(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=20)
    if preflight.returncode:
        report = {"status": "BLOCKED_DOCKER", "free_bytes": free_bytes,
                  "reason": "Docker engine is unavailable; no validation resources started.",
                  "diagnostic": preflight.stderr, "timestamp": datetime.now(timezone.utc).isoformat(),
                  "cleanup": "NOT_REQUIRED"}
        (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"BLOCKED_DOCKER: {output / 'report.json'}", flush=True)
        return 1
    keys = {role: secrets.token_hex(24) for role in ("officer", "developer")}
    checkpoint_key = secrets.token_hex(32)
    database_password = secrets.token_hex(24)
    identities = {keys["officer"]: {"username": "docker-officer", "role": "compliance_officer", "department": "legal_compliance"},
                  keys["developer"]: {"username": "docker-dev", "role": "developer", "department": "engineering"}}
    environment = {**os.environ, "COMPOSE_PROJECT_NAME": project,
                   "API_KEYS": json.dumps(identities), "AUDIT_CHECKPOINT_KEY": checkpoint_key, "KONTEXT_POSTGRES_PASSWORD": database_password, "ALLOWED_ORIGINS": "[]"}
    compose = ["docker", "compose", "-p", project, "-f", str(ROOT/"docker/docker-compose.yml"),
               "-f", str(ROOT/"docker/compose.validation.yml"), "-f", str(ROOT/"docker/compose.hardened.yml")]
    checks = []
    report = {"status": "RUNNING", "scope": "local Docker: FastAPI + PostgreSQL + remote Qdrant",
              "project": project, "checks": checks, "optional_services": "SKIPPED: Ollama and Langfuse are not used by the default request path",
              "production_capacity": "UNVERIFIED", "external_mcp_application": "UNVERIFIED"}

    def redact(text):
        for secret in (*keys.values(), checkpoint_key, database_password):
            text = text.replace(secret, "[REDACTED]")
        return text

    def command(args, label, timeout=300, check=True):
        result = run_bounded(args, cwd=ROOT, env=environment, timeout=timeout)
        (output/(label+".txt")).write_text(redact(result.stdout+result.stderr), encoding="utf-8")
        if check and result.returncode:
            raise RuntimeError(f"{label} failed (exit {result.returncode}); see {label}.txt")
        return result

    def record(name, passed, details=None):
        checks.append({"name": name, "status": "PASS" if passed else "FAIL", "details": details})
        if not passed:
            raise AssertionError(name)

    def fingerprint():
        return source_fingerprint()

    source = fingerprint()
    try:
        print("Building the application image...", flush=True)
        command(compose+["build", "app"], "build", timeout=1800)
        print("Starting isolated application, PostgreSQL and Qdrant...", flush=True)
        command(compose+["up", "-d", "--wait", "--wait-timeout", "180", "postgres", "qdrant"], "dependency-startup", timeout=240)
        migration = command(compose+["run", "--rm", "--no-deps", "app", "python", "-m", "scripts.migrate_db", "upgrade"],
                            "schema-upgrade", timeout=90)
        record("explicit_schema_migration", migration.returncode == 0)
        case = command(compose+["run", "--rm", "--no-deps", "-e", "KONTEXT_VALIDATION_PROJECT="+project,
            "app", "python", "-m", "scripts.validate_postgres_retries", "--fixture-validation"],
            "postgres-retry-case", timeout=120)
        case_report = json.loads(case.stdout.strip().split("\n")[-1])
        (output/"postgres-retry-case.json").write_text(json.dumps(case_report, indent=2), encoding="utf-8")
        record("postgres_concurrent_retry_and_fault_case", case_report["status"] == "PASS",
               {key: value for key, value in case_report.items() if key != "attempts"})
        command(compose+["up", "-d", "--wait", "--wait-timeout", "180", "app"], "startup", timeout=240)
        port = command(compose+["port", "app", "8000"], "port").stdout.strip().rsplit(":", 1)[1]
        base_url = "http://127.0.0.1:"+port
        officer = {"X-API-Key": keys["officer"]}
        developer = {"X-API-Key": keys["developer"]}
        command(compose+["exec", "-T", "app", "python", "-m", "app.db.seed_data"], "seed-validation-fixtures")
        packaging = command(compose+["exec", "-T", "app", "python", "-c",
            "from pathlib import Path; paths=['/app/.env','/app/.git','/app/.venv','/app/data/enterprise_records.db','/app/data/audit_log.jsonl','/app/data/execution_traces.jsonl']; "
            "assert not any(Path(p).exists() for p in paths) and not list(Path('/app').glob('.venv*')); print('Local credentials, virtual environments and runtime records excluded')"], "image-packaging")
        record("image_excludes_local_secrets_and_runtime", packaging.returncode == 0)
        for label, interpreter, evidence_path in (
                ("app", "python", "/opt/kontext-build/app-pip-check.txt"),
                ("sdk", "/opt/mcp-sdk/bin/python", "/opt/kontext-build/sdk-pip-check.txt")):
            checked = command(compose+["exec", "-T", "app", interpreter, "-c",
                "import importlib.util; from pathlib import Path; "
                "assert importlib.util.find_spec('pip') is None; "
                f"evidence=Path({evidence_path!r}).read_text(); assert 'No broken requirements found' in evidence; print(evidence)"],
                label+"-build-package-check")
            record(label+"_build_dependencies_checked_runtime_pip_absent", checked.returncode == 0)

        def tool(client, name, arguments, headers=None):
            response = client.post("/api/v1/tools/call", json={"name": name, "arguments": arguments}, headers=headers)
            response.raise_for_status()
            return response.json()

        with httpx.Client(base_url=base_url, timeout=30, trust_env=False) as client:
            record("health", client.get("/health").json()["status"] == "healthy")
            oversized = client.post("/api/v1/chat", content=b"x"*(1048576+1))
            record("rest_request_admission", oversized.status_code == 413 and "x-request-id" in oversized.headers)
            record("reject_demo_key", client.get("/api/v1/tools/list", headers={"X-API-Key": "key_alice_compliance"}).status_code == 401)
            record("reject_forged_role", client.get("/api/v1/tools/list", headers={"X-User-Role": "admin"}).status_code == 401)
            record("public_cannot_read_private", tool(client, "query_ai_system_compliance", {"system_id": "SYS-HR-001"})["isError"])
            record("developer_department_boundary", tool(client, "query_ai_system_compliance", {"system_id": "SYS-HR-001"}, developer)["isError"])
            hit = client.get("/api/v1/search", params={"q": "Article 5 prohibited practices", "method": "reranked", "top_k": 3})
            record("remote_vector_search", hit.status_code == 200 and any(h["article_id"] == "Article 5" for h in hit.json()["hits"]))
            record("search_enum_validation", client.get("/api/v1/search", params={"q": "Article 5", "method": "unknown"}).status_code == 422
                   and client.get("/api/v1/search", params={"q": "Article 5", "language": "unknown"}).status_code == 422)
            args = {"system_id": "SYS-HR-001", "findings": "Docker validation fixture: explicitly reviewed",
                    "compliance_status": "conditional_pass", "risk_score": 5.5}
            record("schema_rejects_boolean_score", tool(client, "submit_compliance_audit_record", {**args, "risk_score": True}, officer)["isError"])
            record("developer_cannot_write", tool(client, "submit_compliance_audit_record", args, developer)["isError"])
            ids = []
            for _ in range(2):
                result = tool(client, "submit_compliance_audit_record", args, officer)
                record("explicit_postgres_write", not result["isError"])
                ids.append(json.loads(result["content"][0]["text"])["assessment_id"])
            record("unique_assessment_ids", len(set(ids)) == 2)
            retry_args = {**args, "idempotency_key": "docker-retry-fixture"}
            first_retry = tool(client, "submit_compliance_audit_record", retry_args, officer)
            second_retry = tool(client, "submit_compliance_audit_record", retry_args, officer)
            record("postgres_retry_safe_write", not first_retry["isError"] and first_retry["content"] == second_retry["content"])
            conflict = tool(client, "submit_compliance_audit_record", {**retry_args, "risk_score": 8}, officer)
            record("postgres_retry_payload_conflict", conflict["isError"])

            chat = client.post("/api/v1/chat", headers=officer, json={"query": "submit audit"})
            record("chat_cannot_sign_off", chat.status_code == 200 and "Chat does not create" in chat.json()["answer"])
            private_query = "What does Article 9 say for docker-person@example.test?"
            chat = client.post("/api/v1/chat", headers=developer, json={"query": private_query})
            record("chat_response", chat.status_code == 200)
            traces = client.get("/api/v1/audit/traces", headers=developer).json()
            record("trace_privacy_and_ownership", bool(traces) and all(t["user_id"] == "docker-dev" and t["query"] == "[QUERY OMITTED]" for t in traces))

        # Confirm PostgreSQL and Qdrant were actually used, not a fallback.
        inspection = command(compose+["exec", "-T", "app", "python", "-c",
            "import json; from sqlalchemy import text; from app.db.session import engine; from app.retrieval.dense import DenseRetriever; "
            "d=DenseRetriever(); c=d.client.get_collection(d.collection_name); "
            "print(json.dumps({'dialect':engine.dialect.name,'vector_points':c.points_count,'vector_client':type(d.client._client).__name__})); d.client.close()"], "backend-proof")
        backend = json.loads(inspection.stdout.strip().splitlines()[-1])
        record("real_backend_connections", backend["dialect"] == "postgresql" and backend["vector_points"] > 0 and backend["vector_client"] == "QdrantRemote", backend)
        print("Checking restart persistence and signed audit verification...", flush=True)
        command(compose+["restart", "app"], "restart")
        # Docker can assign a new ephemeral host port when a container restarts.
        port = command(compose+["port", "app", "8000"], "restart-port").stdout.strip().rsplit(":", 1)[1]
        base_url = "http://127.0.0.1:"+port
        deadline = time.monotonic()+90
        with httpx.Client(base_url=base_url, timeout=5, trust_env=False) as client:
            while time.monotonic() < deadline:
                try:
                    if client.get("/health").status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                time.sleep(.5)
            else:
                raise RuntimeError("Application did not recover after restart")
            data = json.loads(tool(client, "query_ai_system_compliance", {"system_id": "SYS-HR-001"}, officer)["content"][0]["text"])
            record("postgres_restart_persistence", set(ids).issubset({a["assessment_id"] for a in data["assessments"]}))
            command(compose+["exec", "-T", "app", "python", "-c", "from app.core.audit import AuditLogger; AuditLogger.create_checkpoint()"], "checkpoint")
            verified = client.get("/api/v1/audit/verify", headers=officer)
            record("signed_audit_after_restart", verified.status_code == 200 and verified.json()["is_valid"], verified.json())

        from scripts.local_operations import validate_operations
        print("Checking backups, dependency recovery, HTTP MCP and bounded concurrent load...",flush=True)
        validate_operations(compose,environment,output,base_url,officer,command,record)
        print("Running the regression suite inside the Linux image...", flush=True)
        suite = command(compose+["exec", "-T", "app", "python", "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider", "--junitxml=/tmp/docker-tests.xml"], "container-tests", timeout=300, check=False)
        # Read through exec: docker cp may not expose files on the /tmp tmpfs.
        evidence = command(compose+["exec", "-T", "app", "python", "-c",
            "from pathlib import Path; print(Path('/tmp/docker-tests.xml').read_text())"], "read-test-evidence")
        (output/"docker-tests.xml").write_text(evidence.stdout, encoding="utf-8")
        cases = list(ET.fromstring(evidence.stdout).iter("testcase"))
        failures = sum(c.find("failure") is not None or c.find("error") is not None for c in cases)
        skipped = sum(c.find("skipped") is not None for c in cases)
        record("linux_regression_suite", suite.returncode == 0 and bool(cases) and failures == 0 and skipped == 0,
               {"tests": len(cases), "failures_or_errors": failures, "skipped": skipped,
                "evidence": "docker-tests.xml"})
        command(compose+["exec", "-T", "app", "python", "-c",
            "from importlib.metadata import distributions; "
            "print('\\n'.join(sorted(d.metadata['Name']+'=='+d.version for d in distributions() "
            "if d.metadata['Name'].lower() not in {'pip','setuptools','wheel'})))"], "resolved-dependencies")
        command(compose+["images", "--format", "json"], "images")
        command(["docker", "version", "--format", "{{json .Server}}"], "docker-version")
        record("source_unchanged", source == fingerprint())
        report["status"] = "PASS"
    except Exception as exc:
        report["status"] = "FAIL"
        report["error"] = redact(str(exc))
        print(report["error"], flush=True)
    finally:
        command(compose+["logs", "--no-color", "--tail", "200"], "container-logs", timeout=60, check=False)
        # Only the unique validation project and its disposable volumes are removed.
        cleaned = command(compose+["down", "--volumes", "--remove-orphans"], "cleanup", timeout=120, check=False)
        report["cleanup"] = "PASS" if cleaned.returncode == 0 else "FAIL"
        if cleaned.returncode:
            report["status"] = "FAIL"
        report["source_sha256"] = source
        report["timestamp"] = datetime.now(timezone.utc).isoformat()
        (output/"report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"{report['status']}: {output / 'report.json'}", flush=True)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
