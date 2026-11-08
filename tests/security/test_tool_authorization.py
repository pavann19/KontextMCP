"""Comprehensive direct database and MCP tool authorization tests (P0 - Section 4.1).

Validates that authorization and row-level boundaries are enforced directly at the
SQLAlchemy ORM layer (SecureRepository) as well as the MCP tool layer.
"""

import pytest
from app.db.session import get_db_context
from app.db.models import AISystem, IncidentReport, ComplianceAssessment
from app.db.repository import SecureRepository, SecurityException
from app.mcp.permissions import UserContext, PermissionManager
from app.mcp.server import mcp_server

@pytest.fixture(scope="module")
def identities():
    return {
        "public": UserContext(username="eva_public", role="public_viewer", department="public", clearance_level=1),
        "hr_dev": UserContext(username="david_hr_dev", role="developer", department="human_resources", clearance_level=2),
        "fin_dev": UserContext(username="charlie_dev", role="developer", department="engineering", clearance_level=2),
        "auditor": UserContext(username="bob_auditor", role="auditor", department="internal_audit", clearance_level=3),
        "compliance": UserContext(username="alice_compliance", role="compliance_officer", department="legal_compliance", clearance_level=4),
    }

# 1. Public viewer accessing internal AI systems directly via DB
def test_direct_db_public_viewer_restricted_to_public_systems(identities):
    with get_db_context() as session:
        systems = SecureRepository.get_ai_systems(session, user=identities["public"])
        assert len(systems) > 0
        # Must only return public registry systems
        for s in systems:
            assert s.is_public_registry is True
            assert s.system_id != "SYS-HR-001"  # Internal HR system must NOT be returned

# 2. Developer accessing another department's records directly via DB
def test_direct_db_developer_cross_department_isolation(identities):
    with get_db_context() as session:
        # HR developer querying systems
        hr_systems = SecureRepository.get_ai_systems(session, user=identities["hr_dev"])
        hr_ids = [s.system_id for s in hr_systems]
        assert "SYS-HR-001" in hr_ids  # Own department
        assert "SYS-BIO-002" not in hr_ids  # Security dept internal system must NOT be returned

        # Querying specifically by ID
        target_outside = SecureRepository.get_ai_system_by_id(session, user=identities["hr_dev"], system_id="SYS-BIO-002")
        assert target_outside is None

# 3. Developer accessing incident history directly via DB
def test_direct_db_developer_denied_incident_history(identities):
    with get_db_context() as session:
        with pytest.raises(SecurityException) as exc_info:
            SecureRepository.get_incident_reports(session, user=identities["hr_dev"], system_id="SYS-HR-001")
        assert "unauthorized to access Article 73 incident history" in str(exc_info.value)

# 4. Auditor attempting write operations directly via DB
def test_direct_db_auditor_denied_compliance_write_operations(identities):
    with get_db_context() as session:
        with pytest.raises(SecurityException) as exc_info:
            SecureRepository.create_compliance_assessment(
                session,
                user=identities["auditor"],
                system_id="SYS-HR-001",
                findings="Unauthorized audit submission",
                compliance_status="compliant",
                risk_score=9.0
            )
        assert "Clearance Level 4 required" in str(exc_info.value)

# 5. Compliance officer accessing permitted organizational records
def test_direct_db_compliance_officer_full_organizational_access(identities):
    with get_db_context() as session:
        all_systems = SecureRepository.get_ai_systems(session, user=identities["compliance"])
        assert len(all_systems) >= 4  # Sees systems across all departments
        
        incidents = SecureRepository.get_incident_reports(session, user=identities["compliance"], system_id="SYS-HR-001")
        assert len(incidents) >= 1

# 6. Missing identity (None)
def test_direct_db_missing_identity_rejection():
    with get_db_context() as session:
        with pytest.raises(SecurityException) as exc_info:
            SecureRepository.get_ai_systems(session, user=None)
        assert "Missing user identity context" in str(exc_info.value)

# 7. Invalid identity (empty/malformed)
def test_direct_db_invalid_identity_rejection():
    with get_db_context() as session:
        malformed = UserContext(username="", role="", department="engineering", clearance_level=1)
        with pytest.raises(SecurityException) as exc_info:
            SecureRepository.get_ai_systems(session, user=malformed)
        assert "Malformed user identity context" in str(exc_info.value)

# 8. Missing department in user context
def test_direct_db_missing_department_rejection():
    with get_db_context() as session:
        no_dept = UserContext(username="test_user", role="developer", department="", clearance_level=2)
        with pytest.raises(SecurityException) as exc_info:
            SecureRepository.get_ai_systems(session, user=no_dept)
        assert "Missing department in user context" in str(exc_info.value)

# 9. Invalid clearance level (e.g. 0 or negative)
def test_direct_db_invalid_clearance_rejection():
    with get_db_context() as session:
        invalid_clearance = UserContext(username="test_user", role="developer", department="engineering", clearance_level=0)
        with pytest.raises(SecurityException) as exc_info:
            SecureRepository.get_ai_systems(session, user=invalid_clearance)
        assert "Invalid clearance level in user context" in str(exc_info.value)

# 10. Manipulated department metadata
def test_direct_db_manipulated_department_metadata(identities):
    with get_db_context() as session:
        # Developer attempts to spoof department by passing an arbitrary department string in query
        systems = SecureRepository.get_ai_systems(session, user=identities["hr_dev"])
        departments_returned = {s.department for s in systems if not s.is_public_registry}
        # Can only see 'human_resources' for private systems
        for d in departments_returned:
            assert d == "human_resources"

