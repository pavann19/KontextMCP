> Historical design document. Claims and measurements below predate the current hardening pass and are not current verification evidence. Use [README](../README.md), [hardening scope](hardening.md), and the generated reports for current behavior.

# KontextMCP — Model Context Protocol (MCP) Tool Inventory

**Standard Specification:** Model Context Protocol (MCP) 2024-11-05 & JSON-RPC 2.0  
**Transport:** In-Memory / Stdio / HTTP JSON-RPC 2.0 Gateway  
**Authentication & Authorization:** Dual-Layer RBAC (Clearance 1–4) & ABAC Row-Level Filtering

---

## 1. Enterprise Tool Catalog

### Tool 1: `search_eu_ai_act_provisions`
- **Description:** Performs bilingual German/English statutory search across official EU AI Act provisions, articles, recitals, and annexes using hybrid BM25 + dense vector retrieval and legal cross-reranking.
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "Search query in English or German."},
      "language": {"type": "string", "enum": ["en", "de"], "description": "Optional language filter."},
      "top_k": {"type": "integer", "default": 3, "description": "Number of provisions to retrieve."}
    },
    "required": ["query"]
  }
  ```
- **Required Roles:** `public_viewer`, `developer`, `auditor`, `compliance_officer`, `admin`
- **Minimum Clearance:** Level 1 (Public)
- **Department Restriction:** None (Public Knowledge)
- **Capability:** Read-Only
- **Data Stores Accessed:** `data/chunks/eu_ai_act_chunks.json`, BM25 Okapi Index, Qdrant Vector Collection (`eu_ai_act_bilingual`)
- **Expected Denial Behavior:** None (Public). If missing parameter `query`, returns JSON-RPC `-32602` (Invalid params).

---

### Tool 2: `query_ai_system_compliance`
- **Description:** Queries an enterprise AI system's registration record, risk tier, Annex III classification, conformity assessment history, and operational metadata.
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "system_id": {"type": "string", "description": "Unique system ID (e.g. 'SYS-HR-001') or system name."}
    },
    "required": ["system_id"]
  }
  ```
- **Required Roles:** `public_viewer`, `developer`, `auditor`, `compliance_officer`, `admin`
- **Minimum Clearance:** Level 1 (Public Viewer restricted to public registry systems; Level 2 for departmental access; Level 3+ for enterprise-wide)
- **Department Restriction:**
  - `public_viewer`: Can only read systems where `is_public_registry == True`.
  - `developer`: Can only read systems registered under their assigned department or public systems.
  - `auditor` & `compliance_officer`: Organization-wide visibility across all departments.
- **Capability:** Read-Only
- **Database Tables Accessed:** `ai_systems`, `compliance_assessments`
- **Expected Denial Behavior:**
  - Cross-department or private access violation returns `ROW-LEVEL PERMISSION DENIED` (JSON-RPC code `-32001`).
  - Missing `system_id` returns `-32602` schema validation error.
  - Non-existent system returns `No registered AI system found`.

---

### Tool 3: `list_high_risk_systems`
- **Description:** Lists registered AI systems classified as high-risk under Article 6 and Annex III, filtered by risk tier and optional department.
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "risk_level": {"type": "string", "default": "high_risk", "description": "Filter by risk tier (high_risk, prohibited, minimal_risk)."},
      "department": {"type": "string", "description": "Optional department filter."}
    }
  }
  ```
- **Required Roles:** `developer`, `auditor`, `compliance_officer`, `admin`
- **Minimum Clearance:** Level 2 (Internal Developer)
- **Department Restriction:**
  - `developer`: Filtered results contain only systems in caller's department or public systems.
  - `auditor` & `compliance_officer`: Full cross-department view.
  - `public_viewer`: Access strictly denied.
- **Capability:** Read-Only
- **Database Tables Accessed:** `ai_systems`
- **Expected Denial Behavior:** If invoked by `public_viewer` (Clearance 1), returns `SECURITY VIOLATION: Role 'public_viewer' is not authorized... Minimum clearance required is 2` (JSON-RPC code `-32001`).

---

### Tool 4: `get_system_incident_history`
- **Description:** Accesses confidential Article 73 serious incident reports, malfunctions, fundamental rights breaches, and regulatory reporting statuses.
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "system_id": {"type": "string", "description": "Unique system ID (e.g. 'SYS-HR-001')."}
    },
    "required": ["system_id"]
  }
  ```
- **Required Roles:** `auditor`, `compliance_officer`, `admin`
- **Minimum Clearance:** Level 3 (Auditor)
- **Department Restriction:** None (Auditors and Compliance Officers inspect all departmental incidents).
- **Capability:** Read-Only (High Sensitivity)
- **Database Tables Accessed:** `ai_systems`, `incident_reports`
- **Expected Denial Behavior:** Invocation by `public_viewer` or `developer` returns `SECURITY VIOLATION: Insufficient clearance level for 'get_system_incident_history'. Minimum clearance required is 3` (JSON-RPC code `-32001`).

---

### Tool 5: `submit_compliance_audit_record`
- **Description:** Records an official Article 43 conformity assessment sign-off, establishes compliance status (`compliant`, `conditional_pass`, `non_compliant`), and updates the AI system's official registry conformity status.
- **Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "system_id": {"type": "string", "description": "Target AI system ID."},
      "findings": {"type": "string", "description": "Detailed audit findings and evidence summary."},
      "compliance_status": {"type": "string", "enum": ["compliant", "conditional_pass", "non_compliant"], "description": "Conformity assessment outcome."},
      "risk_score": {"type": "number", "description": "Numeric risk assessment score (0.0 to 10.0)."},
      "remediation_plan": {"type": "string", "description": "Mandatory remediation requirements if conditional or non-compliant."}
    },
    "required": ["system_id", "findings", "compliance_status", "risk_score"]
  }
  ```
- **Required Roles:** `compliance_officer`, `admin`
- **Minimum Clearance:** Level 4 (Compliance Officer)
- **Department Restriction:** Organization-wide authorized officers.
- **Capability:** Read & Write (Mutating Database Transaction)
- **Database Tables Accessed:** `compliance_assessments` (INSERT), `ai_systems` (UPDATE `conformity_status`, `last_audit_date`)
- **Transaction Safety:** Enclosed in SQLAlchemy session transaction with automatic rollback if status is invalid or system ID does not exist.
- **Expected Denial Behavior:** Invocation by any role other than `compliance_officer` or `admin` returns `SECURITY VIOLATION: Insufficient clearance level for 'submit_compliance_audit_record'. Minimum clearance required is 4` (JSON-RPC code `-32001`).
