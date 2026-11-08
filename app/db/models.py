"""SQLAlchemy Database Models for Enterprise AI Act Registry (P6.5)."""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    """Enterprise user with role-based access control attributes."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    full_name = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False)  # public_viewer, developer, auditor, compliance_officer
    department = Column(String(64), nullable=False)
    clearance_level = Column(Integer, default=1)  # 1 (public), 2 (dev), 3 (auditor), 4 (compliance)
    created_at = Column(DateTime, default=datetime.utcnow)

class AISystem(Base):
    """Registered Enterprise AI System subject to EU AI Act compliance."""
    __tablename__ = "ai_systems"
    
    system_id = Column(String(32), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    risk_category = Column(String(64), nullable=False, index=True)  # prohibited, high_risk, specific_transparency_risk, minimal_risk
    annex_category = Column(String(128), nullable=True)  # e.g., Annex III Point 4(a)
    provider_name = Column(String(128), nullable=False)
    deployer_name = Column(String(128), nullable=False)
    department = Column(String(64), nullable=False, index=True)
    intended_purpose = Column(Text, nullable=False)
    conformity_status = Column(String(32), nullable=False, default="under_assessment")  # approved, under_assessment, rejected, not_required
    registration_date = Column(String(32), nullable=False)
    last_audit_date = Column(String(32), nullable=True)
    is_public_registry = Column(Boolean, default=False)
    
    assessments = relationship("ComplianceAssessment", back_populates="ai_system", cascade="all, delete-orphan")
    incidents = relationship("IncidentReport", back_populates="ai_system", cascade="all, delete-orphan")

class ComplianceAssessment(Base):
    """Conformity assessments and audits conducted under Article 43 & Article 11."""
    __tablename__ = "compliance_assessments"
    
    assessment_id = Column(String(32), primary_key=True, index=True)
    system_id = Column(String(32), ForeignKey("ai_systems.system_id"), nullable=False, index=True)
    auditor_id = Column(String(64), nullable=False)
    auditor_name = Column(String(128), nullable=False)
    assessment_type = Column(String(64), nullable=False)  # internal_control, third_party_notified_body, fundamental_rights_impact_assessment
    findings = Column(Text, nullable=False)
    status = Column(String(32), nullable=False)  # compliant, conditional_pass, non_compliant
    risk_score = Column(Float, nullable=False, default=0.0)  # 0.0 to 10.0
    remediation_plan = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    ai_system = relationship("AISystem", back_populates="assessments")

class IncidentReport(Base):
    """Article 73 serious incidents, malfunctions, and fundamental rights breaches."""
    __tablename__ = "incident_reports"
    
    incident_id = Column(String(32), primary_key=True, index=True)
    system_id = Column(String(32), ForeignKey("ai_systems.system_id"), nullable=False, index=True)
    incident_type = Column(String(64), nullable=False)  # serious_incident, malfunction, fundamental_rights_breach, data_leak
    severity = Column(String(32), nullable=False, index=True)  # critical, high, medium, low
    description = Column(Text, nullable=False)
    reported_to_ai_office = Column(Boolean, default=False)
    status = Column(String(32), default="open")  # open, investigating, resolved
    occurred_at = Column(String(32), nullable=False)
    resolved_at = Column(String(32), nullable=True)
    
    ai_system = relationship("AISystem", back_populates="incidents")

class AuditLogRecord(Base):
    """Tamper-evident audit trail table storing tool executions and policy decisions."""
    __tablename__ = "audit_log_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String(64), nullable=False)
    user_role = Column(String(32), nullable=False)
    action = Column(String(64), nullable=False)
    target_resource = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False)  # AUTHORIZED, PERMISSION_DENIED, EXECUTED, ERROR
    details = Column(Text, nullable=False)
    prev_hash = Column(String(64), nullable=False)
    record_hash = Column(String(64), nullable=False, index=True)



class AuditOutboxEvent(Base):
    """Durable audit intent committed atomically with its business transaction."""
    __tablename__ = "audit_outbox"
    __table_args__ = (Index("ix_audit_outbox_delivery_created", "delivered_at", "created_at"),)
    event_id = Column(String(64), primary_key=True)
    payload = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    delivered_at = Column(DateTime, nullable=True, index=True)
    attempts = Column(Integer, default=0, nullable=False)
    last_error = Column(String(128), nullable=True)


class AuditDeliveryReceipt(Base):
    """Atomically acknowledges SQL-mirror delivery for an outbox event."""
    __tablename__ = "audit_delivery_receipts"
    event_id = Column(String(64), primary_key=True)
    record_hash = Column(String(64), nullable=False, unique=True)


class ComplianceWriteReceipt(Base):
    """Caller-scoped retry receipt committed with assessment and audit intent."""
    __tablename__ = "compliance_write_receipts"
    scope_key = Column(String(64), primary_key=True)
    payload_hash = Column(String(64), nullable=False)
    assessment_id = Column(String(32), nullable=False)
