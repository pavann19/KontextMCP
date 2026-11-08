# Reliability follow-up

## Retry-safe compliance writes

Supply `idempotency_key` in `submit_compliance_audit_record` arguments. Reuse the same key and identical fields when retrying after a timeout. The key is optional for existing clients: calls without one still create a new assessment each time.

The receipt is scoped to authenticated username, role and department. It stores hashes of the scope/key and normalized business fields, plus the assessment ID. A unique insert reserves the key before any business mutation. Receipt, assessment, system-status update and audit intent commit or roll back together. Concurrent requests wait on the unique key; a retry returns the original assessment. Reuse with changed fields returns a tool error. Authorization is checked again on every retry, and replay never reverts a later assessment's system status.

The new `compliance_write_receipts` table is additive and created through the existing startup schema initialization. Existing records and tables are preserved. Keep receipts for the full supported retry period; no automatic expiry or deletion is implemented. Responses repeat original business content; timing metadata can differ.

## Audit delivery health

Authorized `/metrics` callers can inspect `kontext_audit_outbox_pending`, `kontext_audit_outbox_oldest_pending_seconds`, `kontext_audit_outbox_failed_pending` and `kontext_audit_outbox_attempts_total`. Age is zero for an empty backlog. Attempts reflect persisted dispatcher bookkeeping. Storage failure reports -1 as unknown rather than a healthy zero. Metric labels contain no caller IDs, event IDs, payloads or exception messages. Authentication/clearance requirements remain in force.

## Reproducible Linux build

`requirements-linux.lock` freezes all Python packages from the earlier passing Linux container environment. `requirements-mcp-client.lock` freezes the separate SDK environment, with Windows-only dependencies marked conditionally. The Dockerfile installs these exact versions; PostgreSQL, Qdrant, Python base and optional Ollama images use immutable registry digests. The Python base/Ollama digests were resolved during this follow-up; PostgreSQL/Qdrant digests come from the previously exercised local images.

`requirements.txt` remains the portable dependency declaration. The Linux lock targets Python 3.11 and does not claim a verified Windows installation. These are version locks, not hashed wheel locks or bit-for-bit image reproduction: operating-system package installation still uses the configured distribution repositories. Review and validate updates deliberately, then refresh the lock files and evidence.

Historical 7 November attempt: the locked-image build remained unverified: Docker reported storage I/O/read-only errors with about 24 MB free on the project drive. The task-owned build client was stopped; no application stack was started by that attempt. The validator now refuses builds below 2 GiB of free workspace storage and preserves timed-out command output so a cleanup timeout cannot silently discard the report. No existing files were deleted, Docker storage pruned or shared services restarted.

## Desktop MCP boundary

The computer-use skill launched VS Code and opened a separate window/folder picker. Native dialog targeting/focus did not behave reliably, so tool discovery and invocation were not completed. The workspace MCP configuration and independent SDK/Inspector checks remain available; they do not substitute for actual desktop invocation. See `artifacts/reports/desktop_mcp_validation.json`.

## Verification

Native tests exercise four concurrent retries, changed-payload rejection, caller isolation, rollback and retry, authorization on replay, preservation of later status, stalled-backlog metrics and unknown storage state. The final generated native reports retain their source fingerprint. Container and desktop gaps remain explicitly blocked rather than marked passed.


## 8 November follow-up

Storage and Docker access are restored. Fresh locked-container validation passed all 34 integration checks and 150 Linux tests without skips; desktop input remains unreliable. Backup/restore, database/vector recovery, retry-safe PostgreSQL writes, HTTP MCP and bounded load passed. The 60-second four-worker workload completed 2,164 requests with zero invalid responses, and disposable cleanup passed. See [current Docker evidence](../artifacts/docker/20261108T052607Z/report.json). CLI execution is bounded even when descendants inherit output handles; missing/unavailable Docker produces a saved preflight report. Native verification and the report index were refreshed. See [current gap follow-up](gap-closure-2026-11-08.md).


## Production-oriented portfolio follow-up

The final local release is documented in [production design](production-design.md), [runbook](operations-runbook.md) and [resume case study](resume-case-study.md). It adds migrations, startup verification and request admission, and passes 37 Docker checks plus 172 tests on each native/Linux platform. The baseline Linux lock was extended with pinned migration tooling; Mako was upgraded to 1.3.12 after the isolated advisory audit found one distinct advisory in 1.3.9 (duplicated by the advisory feed). The original audit is preserved under report history. Earlier counts in this document describe their original validation phase.


## Final image-security follow-up

The current source is verified by [20261108T105838Z](../artifacts/docker/20261108T105838Z/report.json): 39 integration checks, 172 Linux tests, 172 native tests and 2,018 valid mixed requests over 60 seconds. Mako is now pinned to 1.4.3 in the image, packaging bootstrap tools are version-locked, Debian security updates are applied, runtime build compilers are omitted and pip is removed after build-time dependency checks. Local Scout reports 0 high/critical findings, down from 4 high before remediation, with 1 medium and 50 low unfixed findings retained for review. Earlier phase counts and scans remain historical.
