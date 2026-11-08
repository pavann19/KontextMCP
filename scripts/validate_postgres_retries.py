"""Synthetic PostgreSQL fault cases, only inside a named disposable validation project."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
import threading
import time
import uuid
from sqlalchemy import event
from app.config import settings
from app.db.session import engine, get_db_context
from app.db.models import AISystem, ComplianceAssessment, AuditOutboxEvent, AuditDeliveryReceipt, AuditLogRecord
from app.db.repository import SecureRepository
from app.mcp.permissions import UserContext
from app.core.audit import AuditLogger
from app.core.outbox import dispatch_pending


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-validation", action="store_true", required=True)
    parser.parse_args()
    if not os.environ.get("KONTEXT_VALIDATION_PROJECT", "").startswith("kontext-validation-"):
        raise RuntimeError("Disposable project marker required; do not run against user databases.")
    if engine.dialect.name != "postgresql":
        raise RuntimeError("This case study requires actual PostgreSQL.")
    system_id = ("CASE-" + uuid.uuid4().hex[:12]).upper()
    user = UserContext(username="case-study-officer", role="compliance_officer", department="legal", clearance_level=4)
    with get_db_context() as session:
        session.add(AISystem(system_id=system_id, name="Disposable retry fixture", risk_category="high_risk",
            provider_name="Fixture", deployer_name="Fixture", department="legal", intended_purpose="Synthetic validation only",
            registration_date="2026-11-08", is_public_registry=False))
        session.commit()

    def write(key, findings="Synthetic reviewed findings"):
        with get_db_context() as session:
            return SecureRepository.create_compliance_assessment(session, user, system_id, findings,
                "conditional_pass", 4, idempotency_key=key).assessment_id

    attempts = []
    identifiers = []
    for group in range(8):
        key = uuid.uuid4().hex
        barrier = threading.Barrier(8)
        def attempt(number):
            barrier.wait(timeout=20)
            started = time.monotonic()
            identifier = write(key)
            return {"group": group, "attempt": number, "outcome": "ACKNOWLEDGED",
                    "assessment_id": identifier, "elapsed_ms": (time.monotonic()-started)*1000}
        with ThreadPoolExecutor(max_workers=8) as executor:
            rows = list(executor.map(attempt, range(8)))
        assert len({row["assessment_id"] for row in rows}) == 1
        identifiers.append(rows[0]["assessment_id"])
        attempts.extend(rows)
        try:
            write(key, "Changed fields must be rejected")
        except ValueError:
            pass
        else:
            raise AssertionError("Conflicting retry accepted")
    with get_db_context() as session:
        assert session.query(ComplianceAssessment).filter_by(system_id=system_id).count() == 8
        assert session.query(AuditOutboxEvent).filter(AuditOutboxEvent.event_id.in_(identifiers)).count() == 8

    # Deliberately discard the first acknowledgement. This is a simulated client
    # outcome, not a claim that a real TCP response was lost.
    key = uuid.uuid4().hex
    uncertain = write(key)
    assert write(key) == uncertain
    identifiers.append(uncertain)
    def fail_insert(*args):
        raise RuntimeError("Injected transaction rollback")
    key = uuid.uuid4().hex
    event.listen(AuditOutboxEvent, "before_insert", fail_insert)
    try:
        try:
            write(key)
        except RuntimeError:
            pass
        else:
            raise AssertionError("Rollback injection did not execute")
    finally:
        event.remove(AuditOutboxEvent, "before_insert", fail_insert)
    with get_db_context() as session:
        assert session.query(ComplianceAssessment).filter_by(system_id=system_id).count() == 9
    retried = write(key)
    assert write(key) == retried
    identifiers.append(retried)

    # No application worker is running: fault injection cannot race its dispatcher.
    original = AuditLogger.log_event
    injected = []
    def append_then_fail(**kwargs):
        entry = original(**kwargs)
        if not injected:
            injected.append(kwargs["event_id"])
            raise OSError("Injected failure after durable append, before outbox acknowledgement")
        return entry
    AuditLogger.log_event = append_then_fail
    try:
        assert dispatch_pending()["failed"] == 1
    finally:
        AuditLogger.log_event = original
    assert injected
    with get_db_context() as session:
        assert session.get(AuditOutboxEvent, injected[0]).delivered_at is None
    recovery_start = time.monotonic()
    dispatch_pending(); dispatch_pending()
    recovery_seconds = time.monotonic()-recovery_start
    entries = [json.loads(line) for line in settings.AUDIT_LOG_PATH.read_text(encoding="utf-8").split("\n") if line.strip()]
    with get_db_context() as session:
        for identifier in identifiers:
            matching = [row for row in entries if row.get("event_id") == identifier]
            assert len(matching) == 1
            assert session.get(AuditOutboxEvent, identifier).delivered_at is not None
            assert session.get(AuditDeliveryReceipt, identifier) is not None
            assert session.query(AuditLogRecord).filter_by(record_hash=matching[0]["record_hash"]).count() == 1
    assert AuditLogger.verify_integrity()[0]
    report = {"status": "PASS", "timestamp": datetime.now(timezone.utc).isoformat(),
        "scope": "Disposable local PostgreSQL repository writes and outbox fault injection; not production capacity",
        "database": engine.dialect.name, "concurrency": 8, "concurrent_retry_attempts": len(attempts),
        "committed_assessments_from_concurrent_attempts": 8, "duplicate_assessment_effects": 0,
        "payload_conflicts_rejected": 8, "discarded_acknowledgement": "SIMULATED_CLIENT_OUTCOME_REPLAYED",
        "rollback_and_retry": "PASS", "append_before_ack_fault": "INJECTED_AND_RECOVERED",
        "total_case_assessments": len(identifiers), "ledger_records_per_assessment": 1,
        "sql_mirrors_per_assessment": 1, "recovery_seconds": recovery_seconds, "attempts": attempts}
    print(json.dumps(report))


if __name__ == "__main__":
    main()
