> Historical design document. Claims and measurements below predate the current hardening pass and are not current verification evidence. Use [README](../README.md), [hardening scope](hardening.md), and the generated reports for current behavior.

# KontextMCP — STRIDE Threat Model & Security Architecture

**Document Version:** 1.0.0  
**Target Architecture:** Secure Enterprise RAG & MCP Agentic Platform  
**Standard:** STRIDE Methodology & OWASP Top 10 for Large Language Models

---

## 1. System Overview & Trust Boundaries

```
[ UNTRUSTED ZONE: External Client / Web UI / Malicious Caller ]
                      │
   ═══════════════════╪═════════════════════════════════════════════  [Trust Boundary 1: API Gateway]
                      ▼
            [ FastAPI API Gateway ]
            - Header / API Key Authentication
            - Rate Limiting & TLS Termination
                      │
   ═══════════════════╪═════════════════════════════════════════════  [Trust Boundary 2: Agent Execution Core]
                      ▼
          [ LangGraph Agent State Machine ]
          ┌──────────────────────────────────────────────┐
          │ Node 1: Guardrails (PII & Injection)        │
          │ Node 2: Intent Router                        │
          │ Node 3: Hybrid Retrieval                     │
          │ Node 4: MCP Tool Execution                   │
          │ Node 5: Grounded Legal Synthesizer           │
          │ Node 6: Output Guard & Telemetry             │
          └──────────────────────────────────────────────┘
               │                                │
   ════════════╪════════════════════════════════╪══════════════════  [Trust Boundary 3: MCP Protocol & Data Layer]
               ▼                                ▼
     [ Retrieval Backends ]          [ MCP Tool Server (JSON-RPC 2.0) ]
     - BM25 Index (Lexical)          - PermissionManager (RBAC/ABAC)
     - Qdrant Vector DB (Dense)      - SecureRepository (Row-Level Security)
     - Legal Cross-Reranker                     │
                                                ▼
                                     [ Relational DB (PostgreSQL / SQLite) ]
                                     - Registered AI Systems
                                     - Article 73 Incident Logs
                                     - Article 43 Conformity Audits
                                     - SHA-256 Audit Trail
```

---

## 2. STRIDE Threat Analysis

### 2.1 Spoofing (Identity & Roles)
- **Threat:** An attacker crafts HTTP requests claiming `X-User-Role: compliance_officer` or `X-User-Id: alice_compliance` to execute privileged database operations.
- **Impact:** Unauthorized access to sensitive Article 73 incident logs and ability to sign off compliance audits.
- **Mitigation:**
  - Mandatory API key authentication (`DEMO_API_KEYS` mapping).
  - Unauthenticated requests default to `public_viewer` (Clearance Level 1).
  - In production mode, unauthenticated requests with privileged role headers receive `401 Unauthorized`.
  - Identity context is immutable inside the agent state machine.

### 2.2 Tampering (Data & Audit Logs)
- **Threat 1:** An attacker modifies legal documents or seeds malicious instructions into retrieved chunks (Indirect Prompt Injection).
- **Mitigation 1:** `PromptGuard.inspect_document_chunk()` sanitizes all retrieved chunks, stripping `<script>`, Markdown comments, HTML tags, and override commands before synthesis.
- **Threat 2:** An attacker modifies audit logs to conceal unauthorized access.
- **Mitigation 2:** Continuous SHA-256 cryptographic hash chaining ($\text{Hash}_i = \text{SHA256}(\text{Hash}_{i-1} \parallel \text{Payload}_i)$) backed by periodic HMAC-SHA256 signed checkpoints (`audit_checkpoints.json`).

### 2.3 Repudiation
- **Threat:** A compliance officer signs off an unapproved AI system and later claims they never performed the action.
- **Impact:** Legal non-compliance under EU AI Act Article 99.
- **Mitigation:**
  - Every tool execution writes a signed audit record capturing caller `user_id`, `user_role`, `target_resource`, `action`, exact timestamp, and cryptographic hash pointer.
  - Audit logger is thread-safe (`threading.RLock`) preventing dropped or ambiguous records.

### 2.4 Information Disclosure (PII & Cross-Department Data)
- **Threat 1:** Developer from HR accesses Finance department models (`SYS-FIN-001`) or incident logs.
- **Mitigation 1:** Dual-layer enforcement: `PermissionManager` at the MCP protocol boundary and `SecureRepository` at the SQLAlchemy query layer enforce row-level departmental boundaries.
- **Threat 2:** Prompts or outputs leak German Tax IDs (Steuer-ID), IBANs, or emails.
- **Mitigation 2:** `PIIGuard` provides automated masking and reversible session-scoped pseudonymization (`<EMAIL_1>`, `<IBAN_1>`), with automatic session cleanup.

### 2.5 Denial of Service (DoS & Deadlocks)
- **Threat:** Concurrent requests cause deadlocks or database connection starvation; complex queries cause infinite loops.
- **Mitigation:**
  - Upgraded internal locking to re-entrant `threading.RLock()`.
  - LangGraph execution limits: `max_steps = 8`, `max_tool_invocations = 3`, 30-second request timeout.
  - Sub-millisecond BM25 and low-overhead dense search (mean latency < 3.5 ms).

### 2.6 Elevation of Privilege (Jailbreaks & Multi-Turn Persuasion)
- **Threat:** An attacker uses multi-turn conversations, role-play ("You are DAN"), or homoglyph obfuscation to persuade the agent to bypass tool clearance restrictions.
- **Impact:** System prompt leakage, unauthorized tool execution.
- **Mitigation:**
  - Canonical de-obfuscation pipeline in `PromptGuard` (zero-width character removal, Cyrillic/Greek homoglyph mapping, URL decoding, HTML unescaping).
  - Multi-turn persuasion heuristics detecting memory exploitation attempts.
  - Tool authorization enforced by deterministic code inside `MCPServer` and `SecureRepository`, completely independent of the LLM prompt.

---

## 3. Attack Trees

### Attack Tree 1: Indirect Prompt Injection via Poisoned Regulatory Filings
```
[Goal: Force LLM to Exfiltrate Internal Records via Retrieved Context]
  ├── Path A: Exploit Markdown / HTML comments in candidate filings
  │     └── Action: Embed "[comment]: # (SYSTEM OVERRIDE: ...)"
  │     └── Defense: PromptGuard inspects chunks and neutralizes enclosing tags -> Blocked
  ├── Path B: Obfuscate instruction with zero-width characters
  │     └── Action: Insert \u200b between letters of "ignore all rules"
  │     └── Defense: PromptGuard.normalize_text() strips zero-width chars prior to regex -> Blocked
  └── Path C: Split payload across adjacent chunk boundaries
        └── Action: "Ignore all" in Chunk 1, "previous rules" in Chunk 2
        └── Defense: PromptGuard.inspect_multi_chunk_distribution() inspects boundary seams -> Blocked
```

### Attack Tree 2: Unauthorized Cross-Department Database Row Access
```
[Goal: Developer extracts Credit Underwriting AI System Data (Finance)]
  ├── Path A: Direct call to MCP server tools/call bypassing agent
  │     └── Defense: MCPServer checks user.department vs system.department -> Returns 403 Forbidden
  ├── Path B: Prompting agent to call query_ai_system_compliance
  │     └── Defense: Intent router passes user context; tool execution catches denial -> Returns 403
  └── Path C: Direct ORM query via raw session bypassing MCP
        └── Defense: SecureRepository enforces row-level filter in SQLAlchemy query -> Returns None
```
