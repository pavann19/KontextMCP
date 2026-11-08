import json
import pytest
from sqlalchemy import event
from app.db.models import AuditOutboxEvent, ComplianceAssessment
from app.db.repository import SecureRepository
from app.db.session import get_db_context
from app.mcp.permissions import UserContext
from app.core.audit import AuditLogger
from app.core.outbox import dispatch_pending
from app.config import settings

USER=UserContext(username="outbox-test",role="compliance_officer",department="legal",clearance_level=4)


def create():
    with get_db_context() as session:
        return SecureRepository.create_compliance_assessment(session,USER,"SYS-HR-001","Reviewed fixture","conditional_pass",4).assessment_id


def test_transactional_intent_and_retry_after_append(monkeypatch):
    identifier=create()
    with get_db_context() as session:
        assert session.get(ComplianceAssessment,identifier)
        row=session.get(AuditOutboxEvent,identifier)
        assert row and row.delivered_at is None
        payload=json.loads(row.payload)
    # Simulate crash after durable file append but before outbox acknowledgment.
    AuditLogger.log_event(**payload,event_id=identifier)
    dispatch_pending()
    dispatch_pending()
    entries=[json.loads(line) for line in settings.AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines()]
    assert sum(r.get("event_id")==identifier for r in entries)==1
    with get_db_context() as session:
        assert session.get(AuditOutboxEvent,identifier).delivered_at is not None
    assert AuditLogger.verify_integrity()[0]


def test_ledger_failure_keeps_intent_pending(monkeypatch):
    identifier=create()
    original=AuditLogger.log_event
    def fail(*args,**kwargs): raise OSError("injected unavailable ledger")
    monkeypatch.setattr(AuditLogger,"log_event",fail)
    assert dispatch_pending()["failed"] >= 1
    with get_db_context() as session:
        assert session.get(ComplianceAssessment,identifier)
        row=session.get(AuditOutboxEvent,identifier)
        assert row.delivered_at is None and row.last_error=="OSError"
    monkeypatch.setattr(AuditLogger,"log_event",original)
    assert dispatch_pending()["delivered"] >= 1


def test_failed_transaction_commits_neither_record_nor_intent():
    def reject(mapper,connection,target): raise RuntimeError("injected transaction failure")
    with get_db_context() as session:
        before=session.query(ComplianceAssessment).count()
        pending=session.query(AuditOutboxEvent).count()
    event.listen(AuditOutboxEvent,"before_insert",reject)
    try:
        with pytest.raises(RuntimeError): create()
    finally:
        event.remove(AuditOutboxEvent,"before_insert",reject)
    with get_db_context() as session:
        assert session.query(ComplianceAssessment).count()==before
        assert session.query(AuditOutboxEvent).count()==pending


def test_committed_write_remains_successful_during_ledger_outage(monkeypatch):
    from app.mcp.server import mcp_server
    def fail(*args,**kwargs):raise OSError("injected ledger outage")
    monkeypatch.setattr(AuditLogger,"log_event",fail)
    result=mcp_server.call_tool("submit_compliance_audit_record",{"system_id":"SYS-HR-001","findings":"Reviewed explicit fixture","compliance_status":"conditional_pass","risk_score":3},USER)
    assert not result.isError
    assert result.metadata["audit_delivery"]=="DURABLE_OUTBOX"
    identifier=json.loads(result.content[0].text)["assessment_id"]
    with get_db_context() as session:
        assert session.get(ComplianceAssessment,identifier)
        assert session.get(AuditOutboxEvent,identifier).delivered_at is None


def test_crash_before_sql_mirror_is_repaired(monkeypatch):
    from contextlib import contextmanager
    from app.db.models import AuditLogRecord,AuditDeliveryReceipt
    import app.core.audit as module
    identifier=create()
    with get_db_context() as session:payload=json.loads(session.get(AuditOutboxEvent,identifier).payload)
    original=module.get_db_context
    @contextmanager
    def unavailable():
        raise OSError("injected SQL mirror outage")
        yield
    monkeypatch.setattr(module,"get_db_context",unavailable)
    entry=AuditLogger.log_event(**payload,event_id=identifier)
    monkeypatch.setattr(module,"get_db_context",original)
    with get_db_context() as session:
        assert session.query(AuditLogRecord).filter_by(record_hash=entry.record_hash).count()==0
    dispatch_pending();dispatch_pending()
    with get_db_context() as session:
        assert session.query(AuditLogRecord).filter_by(record_hash=entry.record_hash).count()==1
        assert session.get(AuditDeliveryReceipt,identifier)
        assert session.get(AuditOutboxEvent,identifier).delivered_at is not None
