"""Regression checks through the real ASGI routing and dependency boundary."""
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from app.main import app
from app.config import settings
from app.db.session import get_db_context
from app.db.models import ComplianceAssessment
from app.core.audit import AuditLogger
from app.core.pii_guard import pii_guard
from app.core.tracing import telemetry
from app.agent.graph import run_agent_query
from app.mcp.permissions import UserContext
from app.evaluation.evaluator import BenchmarkEvaluator

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "API_KEYS", {
        "test-officer-credential": {"username": "officer", "role": "compliance_officer", "department": "legal"},
        "test-dev-credential": {"username": "dev", "role": "developer", "department": "engineering"}
    })
    with TestClient(app) as connection:
        yield connection

@pytest.mark.parametrize("environment", ["development", "production"])
def test_privilege_requires_provisioned_credentials(client, monkeypatch, environment):
    monkeypatch.setattr(settings, "ENVIRONMENT", environment)
    assert client.get("/api/v1/tools/list", headers={"X-API-Key": "key_alice_compliance"}).status_code == 401
    assert client.get("/api/v1/tools/list", headers={"X-User-Role": "compliance_officer"}).status_code == 401
    response = client.get("/api/v1/tools/list", headers={"X-API-Key": "test-officer-credential", "X-User-Role": "public_viewer"})
    assert any(t["name"] == "submit_compliance_audit_record" for t in response.json())
    assert client.get("/api/v1/audit/verify").status_code == 403
    assert client.get("/api/v1/benchmark/results").status_code == 403


def test_chat_cannot_create_compliance_approval(client):
    with get_db_context() as session:
        before = session.scalar(select(func.count()).select_from(ComplianceAssessment))
    response = client.post("/api/v1/chat", headers={"X-API-Key": "test-officer-credential"},
                           json={"query": "submit audit", "target_language": "de"})
    assert response.status_code == 200
    assert "Chat does not create" in response.json()["answer"]
    with get_db_context() as session:
        assert session.scalar(select(func.count()).select_from(ComplianceAssessment)) == before


def test_write_validates_arguments_and_ids_are_unique(client):
    headers = {"X-API-Key": "test-officer-credential"}
    args = {"system_id": "SYS-HR-001", "findings": "Explicit reviewed test findings",
            "compliance_status": "conditional_pass", "risk_score": 5.5}
    for bad in ({**args, "risk_score": -1}, {**args, "risk_score": True}, {k:v for k,v in args.items() if k != "risk_score"}):
        result = client.post("/api/v1/tools/call", headers=headers, json={"name": "submit_compliance_audit_record", "arguments": bad})
        assert result.json()["isError"]
    ids = []
    for _ in range(2):
        result = client.post("/api/v1/tools/call", headers=headers, json={"name": "submit_compliance_audit_record", "arguments": args})
        assert not result.json()["isError"], result.text
        ids.append(json.loads(result.json()["content"][0]["text"])["assessment_id"])
    assert ids[0] != ids[1]


def test_traces_omit_input_and_are_owner_scoped(client):
    trace = telemetry.start_trace("someone-else", "private@example.com api_key=supersecret123")
    telemetry.end_trace(trace.trace_id)
    response = client.post("/api/v1/chat", headers={"X-API-Key": "test-dev-credential"},
                           json={"query": "Article 9 for confidential@example.com"})
    assert response.status_code == 200
    assert not pii_guard._pseudonym_vaults.get(response.json()["trace_id"])
    data = client.get("/api/v1/audit/traces", headers={"X-API-Key": "test-dev-credential"}).json()
    assert data and all(t["user_id"] == "dev" and t["query"] == "[QUERY OMITTED]" for t in data)
    assert "confidential@example.com" not in telemetry.trace_file.read_text(encoding="utf-8")


def test_failure_cleans_pii_vault_and_trace(monkeypatch):
    from app.agent.graph import agent_executor
    def fail(state, **kwargs):
        pii_guard.pseudonymize("secret@example.com", session_id=state.trace_id)
        raise RuntimeError("injected failure")
    monkeypatch.setattr(agent_executor, "invoke", fail)
    before_vaults = set(pii_guard._pseudonym_vaults)
    before_traces = set(telemetry.active_traces)
    with pytest.raises(RuntimeError):
        run_agent_query("query")
    assert set(pii_guard._pseudonym_vaults) == before_vaults
    assert set(telemetry.active_traces) == before_traces


def test_annex_and_article_matching_is_exact():
    assert not BenchmarkEvaluator._matches_expected_article("Annex I", "Annex III")
    assert not BenchmarkEvaluator._matches_expected_article("Article 5", "Article 50")
    assert BenchmarkEvaluator._matches_expected_article("Anhang III", "Annex 3")
    assert BenchmarkEvaluator._matches_expected_article("Artikel 5", "Article 5")
