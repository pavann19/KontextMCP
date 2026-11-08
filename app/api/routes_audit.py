"""Audit trail query and cryptographic verification endpoints (P6.9)."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel
from app.core.security import resolve_user_context
from app.mcp.permissions import UserContext
from app.core.audit import AuditLogger, AuditEntry
from app.core.tracing import telemetry, ExecutionTrace

router = APIRouter(prefix="/audit", tags=["Security & Audit"])

class IntegrityCheckResponse(BaseModel):
    is_valid: bool
    total_records: int
    error: Optional[str] = None
    verification_status: str

@router.get("/logs", response_model=List[AuditEntry])
def get_audit_logs(
    user_id: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    user: UserContext = Depends(resolve_user_context)
):
    """Queries tamper-evident audit records. Clearance >= 3 (auditor/compliance) required."""
    if user.clearance_level < 3:
        raise HTTPException(
            status_code=403,
            detail=f"SECURITY VIOLATION: Role '{user.role}' lacks clearance to inspect audit logs (Level 3 required)."
        )

    return AuditLogger.query_logs(user_id=user_id, role=role, status=status, limit=limit)

@router.get("/verify", response_model=IntegrityCheckResponse)
def verify_audit_integrity(
    user: UserContext = Depends(resolve_user_context)
):
    """Verifies the SHA-256 cryptographic chaining across the entire audit log."""
    if user.clearance_level < 3:
        raise HTTPException(403, "Audit verification requires auditor clearance.")
    valid, count, err = AuditLogger.verify_integrity()
    if valid:
        valid, err = AuditLogger.verify_checkpoints()
    return IntegrityCheckResponse(
        is_valid=valid,
        total_records=count,
        error=err,
        verification_status="CRYPTOGRAPHIC_CHAIN_VERIFIED" if valid else "TAMPERING_DETECTED"
    )

@router.get("/traces", response_model=List[ExecutionTrace])
def get_telemetry_traces(
    limit: int = Query(20, ge=1, le=100),
    user: UserContext = Depends(resolve_user_context)
):
    """Retrieves execution traces and latency spans for model and tool monitoring."""
    if user.clearance_level < 2:
        raise HTTPException(
            status_code=403,
            detail="Access restricted: Developer or Auditor clearance required."
        )
    return telemetry.get_recent_traces(limit=limit, user_id=user.username)

