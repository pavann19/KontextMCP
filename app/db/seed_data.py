"""Seed data generator for enterprise AI systems and users (P6.5)."""

from datetime import datetime
from app.db.session import init_db, get_db_context
from app.db.models import User, AISystem, ComplianceAssessment, IncidentReport

USERS_SEED = [
    {
        "username": "alice_compliance",
        "full_name": "Dr. Alice Wagner",
        "role": "compliance_officer",
        "department": "legal_compliance",
        "clearance_level": 4
    },
    {
        "username": "bob_auditor",
        "full_name": "Robert Klein",
        "role": "auditor",
        "department": "internal_audit",
        "clearance_level": 3
    },
    {
        "username": "charlie_dev",
        "full_name": "Charlie Miller",
        "role": "developer",
        "department": "engineering",
        "clearance_level": 2
    },
    {
        "username": "david_hr_dev",
        "full_name": "David Mueller",
        "role": "developer",
        "department": "human_resources",
        "clearance_level": 2
    },
    {
        "username": "eva_public",
        "full_name": "Eva Hoffmann",
        "role": "public_viewer",
        "department": "public",
        "clearance_level": 1
    }
]

AI_SYSTEMS_SEED = [
    {
        "system_id": "SYS-HR-001",
        "name": "SmartScreen CV Ranker",
        "risk_category": "high_risk",
        "annex_category": "Annex III Point 4(a) - Employment and worker recruitment",
        "provider_name": "TalentTech AI GmbH",
        "deployer_name": "Enterprise AG",
        "department": "human_resources",
        "intended_purpose": "Automated CV scoring and candidate screening for software engineering roles.",
        "conformity_status": "approved",
        "registration_date": "2026-01-15",
        "last_audit_date": "2026-09-10",
        "is_public_registry": False
    },
    {
        "system_id": "SYS-BIO-002",
        "name": "BioGate Remote Biometric ID",
        "risk_category": "high_risk",
        "annex_category": "Annex III Point 1(a) - Remote biometric identification",
        "provider_name": "SecureVision Systems S.A.",
        "deployer_name": "Enterprise AG",
        "department": "security_operations",
        "intended_purpose": "Real-time automated employee facial verification for high-security lab access.",
        "conformity_status": "under_assessment",
        "registration_date": "2026-02-01",
        "last_audit_date": "2026-08-20",
        "is_public_registry": False
    },
    {
        "system_id": "SYS-CRIT-003",
        "name": "GridFlow Load Balancer",
        "risk_category": "high_risk",
        "annex_category": "Annex III Point 2 - Critical Infrastructure",
        "provider_name": "Siemens Grid Solutions",
        "deployer_name": "Enterprise AG",
        "department": "infrastructure",
        "intended_purpose": "Predictive power grid load balancing and substation failure prevention.",
        "conformity_status": "approved",
        "registration_date": "2025-11-20",
        "last_audit_date": "2026-07-15",
        "is_public_registry": False
    },
    {
        "system_id": "SYS-CHAT-004",
        "name": "Enterprise Customer Support Bot",
        "risk_category": "specific_transparency_risk",
        "annex_category": "Title IV Article 50 - Direct natural person interaction",
        "provider_name": "Conversational Solutions AG",
        "deployer_name": "Enterprise AG",
        "department": "customer_service",
        "intended_purpose": "24/7 customer automated Q&A with synthetic response watermarking.",
        "conformity_status": "approved",
        "registration_date": "2026-03-10",
        "last_audit_date": "2026-09-01",
        "is_public_registry": True
    },
    {
        "system_id": "SYS-TRANS-005",
        "name": "Internal Legal Translator AI",
        "risk_category": "minimal_risk",
        "annex_category": "None - Minimal risk AI system",
        "provider_name": "Enterprise Internal AI Lab",
        "deployer_name": "Enterprise AG",
        "department": "legal_compliance",
        "intended_purpose": "Assisting staff in bilingual English-German draft translations.",
        "conformity_status": "not_required",
        "registration_date": "2026-04-05",
        "last_audit_date": "2026-08-30",
        "is_public_registry": True
    },
    {
        "system_id": "SYS-PROHIB-006",
        "name": "EmotionSense Workplace Monitor",
        "risk_category": "prohibited",
        "annex_category": "Title II Article 5(1)(f) - Workplace emotion recognition",
        "provider_name": "Affective Analytics Inc.",
        "deployer_name": "Enterprise AG",
        "department": "human_resources",
        "intended_purpose": "Facial emotion inference during staff meetings to measure employee engagement.",
        "conformity_status": "rejected",
        "registration_date": "2026-05-12",
        "last_audit_date": "2026-06-01",
        "is_public_registry": False
    }
]

ASSESSMENTS_SEED = [
    {
        "assessment_id": "ASM-2026-001",
        "system_id": "SYS-HR-001",
        "auditor_id": "bob_auditor",
        "auditor_name": "Robert Klein",
        "assessment_type": "internal_control",
        "findings": "Data governance compliance verified pursuant to Article 10. Training datasets evaluated for demographic bias. Disparate impact ratio meets 4/5ths standard. Human oversight override verified.",
        "status": "compliant",
        "risk_score": 8.8,
        "remediation_plan": "Quarterly monitoring of demographic acceptance rates."
    },
    {
        "assessment_id": "ASM-2026-002",
        "system_id": "SYS-BIO-002",
        "auditor_id": "notified_body_tuv_01",
        "auditor_name": "TÜV SÜD Notified Body",
        "assessment_type": "third_party_notified_body",
        "findings": "Annex III point 1(a) high-risk conformity assessment under Article 43. Logging requirements (Article 12) verified. Accuracy metrics for diverse skin tones pending final audit sample.",
        "status": "conditional_pass",
        "risk_score": 6.5,
        "remediation_plan": "Expand test dataset with additional lighting and environmental variance."
    },
    {
        "assessment_id": "ASM-2026-003",
        "system_id": "SYS-PROHIB-006",
        "auditor_id": "alice_compliance",
        "auditor_name": "Dr. Alice Wagner",
        "assessment_type": "internal_control",
        "findings": "PROHIBITED PRACTICE: System attempts emotion recognition in the workplace in direct violation of Article 5(1)(f) of the EU AI Act. No medical or safety derogation applies.",
        "status": "non_compliant",
        "risk_score": 1.2,
        "remediation_plan": "IMMEDIATE DECOMMISSIONING. System barred from deployment. All meeting recording features severed."
    }
]

INCIDENTS_SEED = [
    {
        "incident_id": "INC-2026-001",
        "system_id": "SYS-BIO-002",
        "incident_type": "malfunction",
        "severity": "medium",
        "description": "False negative rejection spike at Lab Entrance B during evening shift due to outdoor infrared glare.",
        "reported_to_ai_office": False,
        "status": "resolved",
        "occurred_at": "2026-08-14 18:32:00",
        "resolved_at": "2026-08-15 10:00:00"
    },
    {
        "incident_id": "INC-2026-002",
        "system_id": "SYS-HR-001",
        "incident_type": "fundamental_rights_breach",
        "severity": "high",
        "description": "Applicant filtering model flagged disproportionate disqualification of candidates with non-German educational certificates. Manual override triggered immediately.",
        "reported_to_ai_office": True,
        "status": "investigating",
        "occurred_at": "2026-09-22 09:15:00",
        "resolved_at": None
    }
]

def seed_database() -> None:
    """Populates the database with initial users, systems, assessments, and incidents."""
    init_db()
    
    with get_db_context() as session:
        # Check users
        for u in USERS_SEED:
            existing = session.query(User).filter_by(username=u["username"]).first()
            if not existing:
                session.add(User(**u))
                
        # Check systems
        for s in AI_SYSTEMS_SEED:
            existing_sys = session.query(AISystem).filter_by(system_id=s["system_id"]).first()
            if not existing_sys:
                session.add(AISystem(**s))
                
        # Check assessments
        for asm in ASSESSMENTS_SEED:
            existing_asm = session.query(ComplianceAssessment).filter_by(assessment_id=asm["assessment_id"]).first()
            if not existing_asm:
                session.add(ComplianceAssessment(**asm))
                
        # Check incidents
        for inc in INCIDENTS_SEED:
            existing_inc = session.query(IncidentReport).filter_by(incident_id=inc["incident_id"]).first()
            if not existing_inc:
                session.add(IncidentReport(**inc))
                
        session.commit()

if __name__ == "__main__":
    seed_database()
    print("Database successfully initialized and seeded with enterprise records.")
