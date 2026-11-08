"""Recoverable delivery of committed audit intents to a deduplicated ledger and SQL mirror."""
import json
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from app.core.audit import AuditLogger
from app.db.models import AuditOutboxEvent, AuditDeliveryReceipt, AuditLogRecord
from app.db.session import get_db_context


def dispatch_pending(limit=100):
    delivered = failed = 0
    with get_db_context() as session:
        identifiers = [row.event_id for row in session.query(AuditOutboxEvent).filter(
            AuditOutboxEvent.delivered_at.is_(None)).order_by(AuditOutboxEvent.created_at).limit(limit).all()]
    for identifier in identifiers:
        with get_db_context() as session:
            row=session.get(AuditOutboxEvent,identifier)
            if row is None or row.delivered_at is not None:continue
            row.attempts+=1
            try:
                entry=AuditLogger.log_event(**json.loads(row.payload),event_id=row.event_id)
                if session.get(AuditDeliveryReceipt,identifier) is None:
                    if session.query(AuditLogRecord).filter(AuditLogRecord.record_hash==entry.record_hash).first() is None:
                        session.add(AuditLogRecord(trace_id=entry.trace_id,timestamp=datetime.fromisoformat(entry.timestamp),
                            user_id=entry.user_id,user_role=entry.user_role,action=entry.action,
                            target_resource=entry.target_resource,status=entry.status,details=entry.details,
                            prev_hash=entry.prev_hash,record_hash=entry.record_hash))
                    session.add(AuditDeliveryReceipt(event_id=identifier,record_hash=entry.record_hash))
                row.delivered_at=datetime.now(timezone.utc)
                row.last_error=None
                session.commit()
                delivered+=1
            except IntegrityError:
                # A competing dispatcher may have atomically mirrored/acknowledged it.
                session.rollback()
                if session.get(AuditDeliveryReceipt,identifier) is not None:delivered+=1
                else:failed+=1
            except Exception as exc:
                session.rollback()
                row=session.get(AuditOutboxEvent,identifier)
                row.attempts+=1;row.last_error=type(exc).__name__
                session.commit();failed+=1
    return {"delivered":delivered,"failed":failed}


def pending_count():
    with get_db_context() as session:
        return session.query(AuditOutboxEvent).filter(AuditOutboxEvent.delivered_at.is_(None)).count()


def delivery_health():
    """Low-cardinality backlog health; never expose event IDs or payloads."""
    from sqlalchemy import func
    with get_db_context() as session:
        pending = session.query(AuditOutboxEvent).filter(AuditOutboxEvent.delivered_at.is_(None))
        count, oldest = pending.with_entities(func.count(AuditOutboxEvent.event_id),
                                             func.min(AuditOutboxEvent.created_at)).one()
        failed = pending.filter(AuditOutboxEvent.last_error.isnot(None)).count()
        attempts = session.query(func.coalesce(func.sum(AuditOutboxEvent.attempts), 0)).scalar()
        age = 0.0
        if oldest is not None:
            if oldest.tzinfo is None:
                oldest = oldest.replace(tzinfo=timezone.utc)
            age = max(0.0, (datetime.now(timezone.utc) - oldest).total_seconds())
        return {"pending": count, "oldest_pending_seconds": age,
                "failed_pending": failed, "attempts": attempts}
