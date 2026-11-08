"""Fine-grained permission and authorization gateway (P6.6).

Enforces Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC)
for MCP tools with row-level data boundaries.
"""

from typing import Dict, Any, Optional, Tuple, List
from pydantic import BaseModel

class UserContext(BaseModel):
    """Execution context of the user invoking the assistant or tool."""
    username: str
    role: str  # public_viewer, developer, auditor, compliance_officer
    department: str
    clearance_level: int = 1

    @classmethod
    def public_default(cls) -> "UserContext":
        return cls(username="anonymous", role="public_viewer", department="public", clearance_level=1)

ROLE_CLEARANCE_MAP = {
    "public_viewer": 1,
    "developer": 2,
    "auditor": 3,
    "compliance_officer": 4,
    "admin": 4
}

TOOL_PERMISSIONS = {
    "search_eu_ai_act_provisions": {
        "min_clearance": 1,
        "allowed_roles": ["public_viewer", "developer", "auditor", "compliance_officer", "admin"],
        "description": "Public search across EU AI Act statutory provisions."
    },
    "query_ai_system_compliance": {
        "min_clearance": 1,
        "allowed_roles": ["public_viewer", "developer", "auditor", "compliance_officer", "admin"],
        "description": "Query registered AI systems. Public viewer limited to public registry; dev limited to dept."
    },
    "list_high_risk_systems": {
        "min_clearance": 2,
        "allowed_roles": ["developer", "auditor", "compliance_officer", "admin"],
        "description": "Lists high-risk systems. Developers limited to their assigned department."
    },
    "get_system_incident_history": {
        "min_clearance": 3,
        "allowed_roles": ["auditor", "compliance_officer", "admin"],
        "description": "Access sensitive malfunction and incident logs under Article 73."
    },
    "submit_compliance_audit_record": {
        "min_clearance": 4,
        "allowed_roles": ["compliance_officer", "admin"],
        "description": "Record an explicitly authorized compliance assessment."
    }
}

class PermissionManager:
    """Enforces authorization checks on tool invocation and applies row-level filters."""

    @classmethod
    def check_tool_access(
        cls,
        tool_name: str,
        user: UserContext
    ) -> Tuple[bool, Optional[str]]:
        """Verifies if user has permission to execute the named tool."""
        policy = TOOL_PERMISSIONS.get(tool_name)
        if not policy:
            return False, f"Unknown tool '{tool_name}' has no defined security policy."

        # Check role membership
        if user.role not in policy["allowed_roles"]:
            return False, (
                f"SECURITY VIOLATION: Role '{user.role}' is not authorized to invoke tool '{tool_name}'. "
                f"Requires one of: {policy['allowed_roles']}."
            )

        # Check clearance level
        min_clearance = policy["min_clearance"]
        if user.clearance_level < min_clearance:
            return False, (
                f"SECURITY VIOLATION: Insufficient clearance level {user.clearance_level} for '{tool_name}'. "
                f"Minimum clearance required is {min_clearance}."
            )

        return True, None

    @classmethod
    def can_access_system_record(
        cls,
        system_dept: str,
        is_public: bool,
        user: UserContext
    ) -> bool:
        """Row-level ABAC rule for accessing a specific AI system."""
        # Compliance officers and auditors see all records
        if user.role in ["compliance_officer", "auditor", "admin"]:
            return True

        # Developers see systems in their own department or public systems
        if user.role == "developer":
            return is_public or (system_dept.lower() == user.department.lower())

        # Public viewers only see public registry entries
        if user.role == "public_viewer":
            return is_public

        return False

