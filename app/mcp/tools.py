"""PostgreSQL/SQLite-backed MCP Tools (P6.5 & P6.6)."""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.db.session import get_db_context
from app.db.models import AISystem, ComplianceAssessment, IncidentReport
from app.db.repository import SecureRepository
from app.mcp.protocol import CallToolResult
from app.mcp.permissions import UserContext, PermissionManager

class MCPToolImplementations:
    """Implementations of enterprise database and knowledge tools."""

    @staticmethod
    def query_ai_system_compliance(
        arguments: Dict[str, Any],
        user: UserContext
    ) -> CallToolResult:
        """Looks up AI system details with row-level ABAC access control."""
        system_id = arguments.get("system_id", "").strip().upper()
        if not system_id:
            return CallToolResult.error("Missing required parameter 'system_id'.")

        with get_db_context() as session:
            system = SecureRepository.get_ai_system_by_id(session, user, system_id)
            if not system:
                return CallToolResult.error(
                    "No registered AI system found or ROW-LEVEL PERMISSION DENIED for this identity."
                )

            # Retrieve associated assessments if permitted
            assessments = []
            if user.clearance_level >= 2:
                for a in system.assessments:
                    assessments.append({
                        "assessment_id": a.assessment_id,
                        "type": a.assessment_type,
                        "status": a.status,
                        "risk_score": a.risk_score,
                        "findings": a.findings,
                        "remediation": a.remediation_plan
                    })

            data = {
                "system_id": system.system_id,
                "name": system.name,
                "risk_category": system.risk_category,
                "annex_category": system.annex_category,
                "provider": system.provider_name,
                "deployer": system.deployer_name,
                "department": system.department,
                "intended_purpose": system.intended_purpose,
                "conformity_status": system.conformity_status,
                "registration_date": system.registration_date,
                "last_audit_date": system.last_audit_date,
                "is_public_registry": system.is_public_registry,
                "assessments_count": len(system.assessments),
                "assessments": assessments
            }
            return CallToolResult.success(json.dumps(data, indent=2))

    @staticmethod
    def list_high_risk_systems(
        arguments: Dict[str, Any],
        user: UserContext
    ) -> CallToolResult:
        """Lists high-risk systems subject to Annex III compliance."""
        risk_level = arguments.get("risk_level", "high_risk").lower() if arguments.get("risk_level") else None
        target_dept = arguments.get("department")

        with get_db_context() as session:
            systems = SecureRepository.get_ai_systems(session, user, risk_category=risk_level)
            filtered_systems = [
                {"system_id": row.system_id, "name": row.name, "risk_category": row.risk_category,
                 "department": row.department, "conformity_status": row.conformity_status,
                 "annex_category": row.annex_category}
                for row in systems if not target_dept or row.department == target_dept
            ]

            return CallToolResult.success(
                json.dumps({
                    "total_found": len(filtered_systems),
                    "requesting_role": user.role,
                    "systems": filtered_systems
                }, indent=2)
            )

    @staticmethod
    def get_system_incident_history(
        arguments: Dict[str, Any],
        user: UserContext
    ) -> CallToolResult:
        """Retrieves Article 73 serious incident reports for an AI system."""
        system_id = arguments.get("system_id", "").strip().upper()
        if not system_id:
            return CallToolResult.error("Missing required parameter 'system_id'.")

        with get_db_context() as session:
            incidents = SecureRepository.get_incident_reports(session, user, system_id)
            system = SecureRepository.get_ai_system_by_id(session, user, system_id)
            if not system:
                return CallToolResult.error(f"System '{system_id}' not found or access denied.")
            inc_data = []
            for inc in incidents:
                inc_data.append({
                    "incident_id": inc.incident_id,
                    "type": inc.incident_type,
                    "severity": inc.severity,
                    "description": inc.description,
                    "reported_to_ai_office": inc.reported_to_ai_office,
                    "status": inc.status,
                    "occurred_at": inc.occurred_at,
                    "resolved_at": inc.resolved_at
                })

            return CallToolResult.success(
                json.dumps({
                    "system_id": system_id,
                    "system_name": system.name,
                    "incident_count": len(inc_data),
                    "incidents": inc_data
                }, indent=2)
            )

    @staticmethod
    def submit_compliance_audit_record(
        arguments: Dict[str, Any],
        user: UserContext
    ) -> CallToolResult:
        """Records an official compliance audit sign-off (Clearance 4 required)."""
        system_id = arguments.get("system_id", "").strip().upper()
        findings = arguments.get("findings", "").strip()
        compliance_status = arguments.get("compliance_status", "").strip().lower()
        risk_score = arguments.get("risk_score")
        remediation_plan = arguments.get("remediation_plan")

        if not system_id or not findings or not compliance_status:
            return CallToolResult.error("Missing mandatory fields (system_id, findings, compliance_status).")

        valid_statuses = ["compliant", "conditional_pass", "non_compliant"]
        if compliance_status not in valid_statuses:
            return CallToolResult.error(f"Invalid compliance_status. Allowed: {valid_statuses}")

        with get_db_context() as session:
            new_assessment = SecureRepository.create_compliance_assessment(
                session, user, system_id, findings, compliance_status, risk_score, remediation_plan,
                idempotency_key=arguments.get("idempotency_key")
            )
            assessment_id = new_assessment.assessment_id
            system = SecureRepository.get_ai_system_by_id(session, user, system_id)

            return CallToolResult.success(
                json.dumps({
                    "status": "RECORD_CREATED",
                    "assessment_id": assessment_id,
                    "system_id": system_id,
                    "auditor": user.username,
                    "conformity_status": {"compliant": "approved", "non_compliant": "rejected",
                                          "conditional_pass": "under_assessment"}[new_assessment.status],
                    "message": "Compliance audit record successfully logged into enterprise registry."
                }, indent=2)
            )

    @staticmethod
    def search_eu_ai_act_provisions(
        arguments: Dict[str, Any],
        user: UserContext
    ) -> CallToolResult:
        """Tool endpoint for RAG search across EU AI Act articles."""
        query = arguments.get("query", "").strip()
        language = arguments.get("language")
        top_k = int(arguments.get("top_k", 3))

        if not query:
            return CallToolResult.error("Missing required parameter 'query'.")

        from app.agent.nodes import get_retrieval_engine
        hybrid, reranker = get_retrieval_engine()
        candidates = hybrid.search(query, top_k=top_k * 2, language=language)

        reranked = reranker.rerank(query, candidates, top_n=top_k, target_language=language)

        results = []
        for chunk, score in reranked:
            results.append({
                "article_id": chunk.article_id,
                "title": chunk.title,
                "language": chunk.language,
                "score": round(score, 4),
                "content": chunk.full_content
            })

        return CallToolResult.success(json.dumps(results, indent=2))

