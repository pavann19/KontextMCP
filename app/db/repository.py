"""Secure Database Repository Layer (P6.5 & P6.6).

Enforces server-side Row-Level Authorization (RBAC & ABAC) directly at the
SQLAlchemy ORM query layer, ensuring unauthorized database rows are never returned
even if a caller accesses database session interfaces directly without MCP.
"""

import hashlib
import json
import math
import uuid
from typing import List, Optional, Tuple
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.db.models import AISystem, IncidentReport, ComplianceAssessment, AuditOutboxEvent, ComplianceWriteReceipt
from app.mcp.permissions import UserContext, PermissionManager

class SecurityException(Exception):
    """Raised when an unauthorized database access attempt is detected."""
    pass

class SecureRepository:
    """Security-scoped repository enforcing row-level ABAC and RBAC on database operations."""

    @staticmethod
    def validate_user_context(user: Optional[UserContext]) -> UserContext:
        """Validates that a caller provides a complete, legitimate UserContext."""
        if user is None:
            raise SecurityException("Access Denied: Missing user identity context.")
        if not getattr(user, "username", None) or not getattr(user, "role", None):
            raise SecurityException("Access Denied: Malformed user identity context.")
        if not getattr(user, "department", None):
            raise SecurityException("Access Denied: Missing department in user context.")
        if getattr(user, "clearance_level", None) is None or user.clearance_level < 1:
            raise SecurityException("Access Denied: Invalid clearance level in user context.")
        return user

    @classmethod
    def get_ai_systems(
        cls,
        session: Session,
        user: Optional[UserContext],
        system_id: Optional[str] = None,
        risk_category: Optional[str] = None
    ) -> List[AISystem]:
        """Queries registered AI systems subject to row-level departmental and role boundaries."""
        user_ctx = cls.validate_user_context(user)
        query = session.query(AISystem)

        if system_id:
            query = query.filter(
                or_(AISystem.system_id == system_id.upper(), AISystem.name.ilike(f"%{system_id}%"))
            )

        if risk_category:
            query = query.filter(AISystem.risk_category == risk_category.lower())

        # Enforce Row-Level Security at Database Query Layer
        if user_ctx.role in ["compliance_officer", "auditor", "admin"]:
            # Enterprise-wide visibility
            pass
        elif user_ctx.role == "developer":
            # Developer visibility: own department systems OR public registry systems
            query = query.filter(
                or_(
                    AISystem.department == user_ctx.department.lower(),
                    AISystem.is_public_registry == True
                )
            )
        elif user_ctx.role == "public_viewer":
            # Public viewer: only public registry systems
            query = query.filter(AISystem.is_public_registry == True)
        else:
            # Unknown role: deny all rows
            return []

        return query.all()

    @classmethod
    def get_ai_system_by_id(
        cls,
        session: Session,
        user: Optional[UserContext],
        system_id: str
    ) -> Optional[AISystem]:
        """Retrieves a single AI system if authorized under row-level boundaries."""
        results = cls.get_ai_systems(session, user, system_id=system_id)
        return results[0] if results else None

    @classmethod
    def get_incident_reports(
        cls,
        session: Session,
        user: Optional[UserContext],
        system_id: str
    ) -> List[IncidentReport]:
        """Retrieves Article 73 incident reports. Requires minimum Clearance Level 3."""
        user_ctx = cls.validate_user_context(user)
        
        # Clearance & Role check: only auditors, compliance officers, and admins may view incident logs
        if user_ctx.clearance_level < 3 or user_ctx.role not in ["auditor", "compliance_officer", "admin"]:
            raise SecurityException(
                f"SECURITY VIOLATION: Role '{user_ctx.role}' with clearance {user_ctx.clearance_level} "
                f"is unauthorized to access Article 73 incident history. Minimum clearance required is 3."
            )

        # Verify system exists
        sys_record = session.query(AISystem).filter(AISystem.system_id == system_id.upper()).first()
        if not sys_record:
            return []

        return session.query(IncidentReport).filter(IncidentReport.system_id == system_id.upper()).all()

    @classmethod
    def create_compliance_assessment(
        cls,
        session: Session,
        user: Optional[UserContext],
        system_id: str,
        findings: str,
        compliance_status: str,
        risk_score: float,
        remediation_plan: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> ComplianceAssessment:
        """Records an explicit assessment; software authorization is not legal approval."""
        user_ctx = cls.validate_user_context(user)

        if user_ctx.clearance_level < 4 or user_ctx.role not in ["compliance_officer", "admin"]:
            raise SecurityException(
                f"SECURITY VIOLATION: Role '{user_ctx.role}' with clearance {user_ctx.clearance_level} "
                f"is unauthorized to execute compliance assessment sign-offs. Clearance Level 4 required."
            )

        system = session.query(AISystem).filter(AISystem.system_id == system_id.upper()).first()
        if not system:
            raise ValueError(f"Target system '{system_id}' does not exist.")

        if compliance_status not in {"compliant", "conditional_pass", "non_compliant"}:
            raise ValueError("Invalid compliance_status.")
        if not isinstance(findings, str) or not findings.strip():
            raise ValueError("Explicit nonempty findings are required.")
        if isinstance(risk_score, bool) or not isinstance(risk_score, (int, float)) or not math.isfinite(risk_score) or not 0 <= risk_score <= 10:
            raise ValueError("risk_score must be a finite number between 0 and 10.")
        import datetime
        assessment_id = f"ASM-{uuid.uuid4().hex[:28]}"
        if idempotency_key is not None:
            if not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key) <= 128 or not idempotency_key.strip():
                raise ValueError("idempotency_key must contain 1 to 128 characters.")
            scope_key = hashlib.sha256(json.dumps([
                user_ctx.username, user_ctx.role, user_ctx.department, idempotency_key
            ], ensure_ascii=False).encode()).hexdigest()
            payload_hash = hashlib.sha256(json.dumps([
                system_id.upper(), findings, compliance_status, float(risk_score), remediation_plan
            ], ensure_ascii=False).encode()).hexdigest()

            def replay(receipt):
                if receipt.payload_hash != payload_hash:
                    raise ValueError("Idempotency key already used with different assessment fields.")
                existing = session.get(ComplianceAssessment, receipt.assessment_id)
                if existing is None:
                    raise ValueError("Idempotency receipt has no committed assessment.")
                return existing

            receipt = session.get(ComplianceWriteReceipt, scope_key)
            if receipt is not None:
                return replay(receipt)
            session.add(ComplianceWriteReceipt(scope_key=scope_key, payload_hash=payload_hash,
                                               assessment_id=assessment_id))
            try:
                # Reserve before mutating business rows. A concurrent winner must
                # commit or roll back before this unique insert can complete.
                session.flush()
            except IntegrityError:
                session.rollback()
                receipt = session.get(ComplianceWriteReceipt, scope_key)
                if receipt is None:
                    raise
                return replay(receipt)

        assessment = ComplianceAssessment(
            assessment_id=assessment_id,
            system_id=system_id.upper(),
            auditor_id=user_ctx.username,
            auditor_name=user_ctx.username,
            assessment_type="internal_control",
            findings=findings,
            status=compliance_status,
            risk_score=risk_score,
            remediation_plan=remediation_plan
        )
        session.add(assessment)

        # Update system status
        system.last_audit_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        if compliance_status == "compliant":
            system.conformity_status = "approved"
        elif compliance_status == "non_compliant":
            system.conformity_status = "rejected"
        else:
            system.conformity_status = "under_assessment"

        session.add(AuditOutboxEvent(event_id=assessment_id, payload=json.dumps({
            "user_id": user_ctx.username, "user_role": user_ctx.role,
            "action": "COMPLIANCE_ASSESSMENT_COMMITTED", "status": "EXECUTED",
            "target_resource": system_id.upper(),
            "details": f"Assessment {assessment_id} committed; status={compliance_status}."
        })))
        session.commit()
        return assessment

