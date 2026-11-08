"""Readiness and low-cardinality operational metrics."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import text
from app.db.session import engine
from app.mcp.permissions import UserContext
from app.core.security import resolve_user_context
from app.core.outbox import delivery_health
from app.core.admission import REJECTIONS

router=APIRouter()
COUNTS={"requests":0,"server_errors":0,"latency_seconds":0.0}


@router.get("/ready")
def ready():
    try:
        with engine.connect() as connection:connection.execute(text("SELECT 1"))
        from app.agent.nodes import get_retrieval_engine
        retriever,_=get_retrieval_engine()
        retriever.dense.client.get_collection(retriever.dense.collection_name)
        if not retriever.bm25.chunks:raise RuntimeError("Empty corpus")
        return {"status":"ready","database":"available","retrieval":"available"}
    except Exception as exc:
        raise HTTPException(503,"A required dependency is unavailable.") from exc


@router.get("/metrics",response_class=PlainTextResponse)
def metrics(user:UserContext=Depends(resolve_user_context)):
    if user.clearance_level<2:raise HTTPException(403,"Operational metrics require developer clearance.")
    try:
        delivery=delivery_health()
    except Exception:
        delivery=dict.fromkeys(("pending", "oldest_pending_seconds", "failed_pending", "attempts"), -1)
    return (f"kontext_http_requests_total {COUNTS['requests']}\n"
            f"kontext_http_server_errors_total {COUNTS['server_errors']}\n"
            f"kontext_http_duration_seconds_sum {COUNTS['latency_seconds']}\n"
            f"kontext_audit_outbox_pending {delivery['pending']}\n"
            f"kontext_audit_outbox_oldest_pending_seconds {delivery['oldest_pending_seconds']}\n"
            f"kontext_audit_outbox_failed_pending {delivery['failed_pending']}\n"
            f"kontext_audit_outbox_attempts_total {delivery['attempts']}\n" +
            "".join(f'kontext_admission_rejections_total{{reason="{reason}"}} {count}\n'
                    for reason, count in REJECTIONS.items()))
