# Current hardening scope - 8 November 2026

The application uses server-owned credentials and scoped repository access. Chat cannot submit compliance sign-offs. Explicit writes validate fields and atomically commit their audit intent in a database outbox. The dispatcher retries and deduplicates ledger delivery, then repairs the SQL mirror and delivery receipt. This is eventual delivery across stores, not a cross-store transaction.

Audit appends use interprocess locking and hash chaining. HMAC checkpoints verify the actual prefix; separate Ed25519 export tooling signs writer-locked snapshots and verifies them against an independently pinned public key. External key/anchor custody remains an operator responsibility. Missing files and tampering fail verification.

Telemetry omits queries, hashes supplied session IDs, restricts trace reads to their owner and clears temporary PII mappings. Retention tooling inventories existing history, creates encrypted quarantine archives and validates reviewed manifests before deletion. This task preserved existing history.

Extractive output validates quotation text and source metadata. Optional Ollama source selection accepts only known chunk IDs and falls back safely; it cannot generate new legal claims or authorize tools. The separate official publication corpus preserves downloaded HTML and supports exact reparse checks. Curated text differs from official text; source fidelity does not establish legal correctness.

Stateless HTTP MCP validates hosts, origins, protocol headers and bounded bodies. Official SDK clients exercise stdio and HTTP; Inspector CLI passes. Actual desktop UI invocation remains unverified.

The hardened Docker profile runs the application as a non-root user with a read-only root filesystem, bounded resources, dropped capabilities and a dedicated writable data volume. Readiness checks dependencies; private metrics expose operational counters. The disposable runner exercises fixture backup/restore, dependency outage recovery and bounded concurrent mixed requests. Production operation, long-duration capacity and cloud deployment remain unverified.

The native suite passes 172 tests without skips. Caller-scoped idempotency receipts prevent duplicate assessments when clients retry with the same key; monitoring exposes stalled delivery age and failed pending intents. Dependency locks and pinned images are prepared, with fresh locked-container verification passing 39 integration checks and 172 Linux tests without skips. See [follow-up](reliability-follow-up.md). Fixed and generated adversarial cases establish only their measured outcomes. The frozen 24-question holdout is agent-authored, and an eight-case model entailment calibration scored only 50%. Independent legal review and universal prompt-injection/PII guarantees remain unestablished. Real Ollama generation passed; Langfuse live operation is blocked by its local memory requirement.

See [README](../README.md), [implementation checklist](implementation-checklist.md), [source manifest](../artifacts/reports/run_manifest.json) and [Docker evidence](docker-validation.md). Historical reports retain their original source boundaries. Existing architecture/security documents predate this pass and should not override the current evidence.


The production-oriented follow-up adds explicit Alembic migrations and startup drift verification, fail-closed deployment settings, global host/body/deadline/admission controls, query-free structured access records and private rejection metrics. Default access logging is disabled in the supplied launchers. Normal server startup does not seed demonstration records, and report GETs never launch benchmark work. The isolated known-advisory audit passes on 91 app and 29 SDK pins after upgrading the vulnerable Mako tooling version. See [design and boundaries](production-design.md).


Final image remediation upgrades Mako to 1.4.3, applies Debian security updates, removes build compilers and removes pip from both runtime interpreters after compatibility checks. Local Scout findings fell from 4 high to 0 high/critical; 1 medium and 50 low findings remain with no reported fixes and require deployment review. The Python advisory scan now also covers the packaging-bootstrap lock.
