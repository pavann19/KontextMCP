import json
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import event
from app.db.models import ComplianceAssessment, AuditOutboxEvent, AISystem
from app.db.repository import SecureRepository
from app.db.session import get_db_context
from app.mcp.permissions import UserContext
from app.mcp.server import mcp_server

USER = UserContext(username="retry-test", role="compliance_officer", department="legal", clearance_level=4)


def write(key, user=USER, findings="Reviewed retry fixture"):
    with get_db_context() as session:
        return SecureRepository.create_compliance_assessment(session, user, "SYS-HR-001",
            findings, "conditional_pass", 4, idempotency_key=key).assessment_id


def test_concurrent_retries_commit_one_assessment_and_intent():
    key = uuid.uuid4().hex
    with get_db_context() as session:
        before = session.query(ComplianceAssessment).count()
        intents = session.query(AuditOutboxEvent).count()
    with ThreadPoolExecutor(max_workers=4) as executor:
        ids = list(executor.map(lambda _: write(key), range(4)))
    assert len(set(ids)) == 1
    with get_db_context() as session:
        assert session.query(ComplianceAssessment).count() == before + 1
        assert session.query(AuditOutboxEvent).count() == intents + 1


def test_key_conflict_and_identity_isolation():
    key = uuid.uuid4().hex
    first = write(key)
    with pytest.raises(ValueError, match="different assessment fields"):
        write(key, findings="Changed conclusion")
    other = USER.model_copy(update={"username": "another-officer"})
    assert write(key, user=other) != first


def test_retry_receipt_rolls_back_with_business_transaction():
    key = uuid.uuid4().hex
    def fail(*args):
        raise RuntimeError("fixture transaction failure")
    event.listen(AuditOutboxEvent, "before_insert", fail)
    try:
        with pytest.raises(RuntimeError):
            write(key)
    finally:
        event.remove(AuditOutboxEvent, "before_insert", fail)
    first = write(key)
    assert write(key) == first


def test_tool_retry_returns_original_result_after_later_assessment():
    args = dict(system_id="SYS-HR-001", findings="Explicit review", compliance_status="compliant",
                risk_score=2, idempotency_key=uuid.uuid4().hex)
    first = mcp_server.call_tool("submit_compliance_audit_record", args, USER)
    assert not first.isError
    write(uuid.uuid4().hex)
    replay = mcp_server.call_tool("submit_compliance_audit_record", args, USER)
    assert not replay.isError
    assert json.loads(first.content[0].text) == json.loads(replay.content[0].text)
    with get_db_context() as session:
        assert session.get(AISystem, "SYS-HR-001").conformity_status == "under_assessment"
    denied = mcp_server.call_tool("submit_compliance_audit_record", args,
                                 USER.model_copy(update={"clearance_level": 1}))
    assert denied.isError

    for bad in ("", " " * 3, "x" * 129):
        result = mcp_server.call_tool("submit_compliance_audit_record", {**args, "idempotency_key": bad}, USER)
        assert result.isError
