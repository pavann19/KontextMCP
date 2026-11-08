import json
from fastapi.testclient import TestClient
import httpx
from app.main import app
from app.config import settings
from app.agent.llm import local_llm


def test_readiness_and_private_metrics():
    with TestClient(app) as client:
        assert client.get("/ready").status_code==200
        assert client.get("/metrics").status_code==403


def test_model_cannot_select_unknown_sources(monkeypatch):
    def response(*args,**kwargs):
        return httpx.Response(200,json={"response":json.dumps({"chunk_ids":["invented-source"]})},request=httpx.Request("POST","http://localhost"))
    monkeypatch.setattr(httpx,"post",response)
    assert local_llm.select_chunks("question",[{"chunk_id":"known","article_id":"Article 9","text":"Known fixture"}]) is None


def test_remote_trace_export_detects_partial_rejection(monkeypatch):
    from app.core.tracing import TelemetryManager
    class Client:
        def __init__(self,*args,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def post(self,*args,**kwargs):
            assert kwargs["json"]["batch"][0]["body"]["input"]=="[QUERY OMITTED]"
            return httpx.Response(207,json={"errors":[{"message":"fixture rejection"}]},request=httpx.Request("POST","http://localhost"))
    monkeypatch.setattr(httpx,"Client",Client)
    manager=TelemetryManager()
    trace=manager.start_trace("test","sensitive@example.com")
    assert manager._send_to_langfuse(trace) is False


def test_delivery_health_reports_stalled_backlog_without_payloads():
    from datetime import datetime, timedelta, timezone
    from app.core.outbox import delivery_health
    from app.db.models import AuditOutboxEvent
    from app.db.session import get_db_context
    import uuid
    identifier = "health-" + uuid.uuid4().hex
    with get_db_context() as session:
        session.add(AuditOutboxEvent(event_id=identifier, payload="sensitive fixture",
            created_at=datetime.now(timezone.utc)-timedelta(minutes=5), attempts=3, last_error="OSError"))
        session.commit()
    try:
        health = delivery_health()
        assert health["pending"] >= 1 and health["failed_pending"] >= 1
        assert health["oldest_pending_seconds"] >= 299 and health["attempts"] >= 3
        assert "sensitive" not in str(health) and identifier not in str(health)
    finally:
        with get_db_context() as session:
            session.query(AuditOutboxEvent).filter_by(event_id=identifier).delete()
            session.commit()


def test_delivery_metrics_expose_health_and_mark_storage_failure(monkeypatch):
    import app.api.routes_operations as operations
    from app.mcp.permissions import UserContext
    user = UserContext(username="operator", role="developer", department="engineering", clearance_level=2)
    monkeypatch.setattr(operations, "delivery_health", lambda: {
        "pending": 2, "oldest_pending_seconds": 301, "failed_pending": 1, "attempts": 4})
    text = operations.metrics(user)
    assert "kontext_audit_outbox_oldest_pending_seconds 301\n" in text
    assert "kontext_audit_outbox_failed_pending 1\n" in text
    def unavailable():
        raise OSError("fixture storage outage")
    monkeypatch.setattr(operations, "delivery_health", unavailable)
    text = operations.metrics(user)
    assert "kontext_audit_outbox_pending -1\n" in text
    assert "kontext_audit_outbox_oldest_pending_seconds -1\n" in text
