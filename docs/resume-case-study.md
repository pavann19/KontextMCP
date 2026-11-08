# Resume and interview case study

## Positioning

**KontextMCP — Backend reliability and security for an MCP-enabled document system**

Python, FastAPI, PostgreSQL, Qdrant, SQLAlchemy/Alembic, LangGraph, MCP and Docker.

Lead with correctness under retries and failures. The retrieval domain supplies a realistic workload, while the database, audit and operations work demonstrate backend/platform decisions. Describe deployment as locally validated. Do not claim production users, a managed SLA, legal approval, trained semantic embeddings, a neural reranker or hosted CI execution without corresponding evidence.

## X–Y–Z evidence

| Accomplishment (X) | Measurement (Y) | Mechanism (Z) |
| --- | --- | --- |
| Prevent duplicate assessment effects during concurrent retries | 64 synthetic PostgreSQL retry attempts, 8 committed assessments, zero duplicate assessment effects; 8 payload conflicts rejected | Caller-scoped idempotency receipts, unique reservation before mutation and one SQL transaction for assessment/status/audit intent |
| Recover audit delivery across an interruption boundary | 10 committed case assessments each retained one ledger event and one SQL mirror after injected append-before-ack failure and replay | Durable outbox, event-ID deduplication, fsynced hash-chained ledger and atomic delivery receipts |
| Verify service behavior under concurrent local requests | 2,018 requests over 60 seconds with four workers and zero invalid responses in the final local run | Hardened non-root deployment, authenticated tools, readiness, dependency recovery, backup restoration and real SDK HTTP checks |
| Reduce reported high-severity image findings | Same local Scout version: 4 high findings before hardening, 0 high/critical after; unfixed medium/low findings retained | Debian security updates, patched packaging/Mako pins, removal of build compilers and runtime pip |

The PostgreSQL case includes an intentionally discarded acknowledgement; this is a **simulated client outcome**, not a measured real-network packet loss. The ledger fault is injected in a one-off fixture process with no competing application worker. These are bounded correctness experiments, not a throughput benchmark or proof that every possible failure is covered.

## Resume bullets

- Prevented duplicate compliance-record effects across **64 PostgreSQL retry attempts at eight-way concurrency**, yielding **8 committed assessments and zero duplicates**, by implementing caller-scoped idempotency receipts and atomic assessment/audit-outbox transactions.
- Preserved **one ledger record and one SQL mirror for each of 10 committed assessments** through injected delivery failure and replay by combining a durable outbox, event-ID deduplication and fsynced hash-chained audit logging.

These are local synthetic-test results. Keep that scope visible in the project description or an adjacent “locally validated” qualifier. The final run is [20261108T105838Z](../artifacts/docker/20261108T105838Z/report.json), with 39 integration checks and 172 Linux tests; its source fingerprint matches. Avoid percentage improvements without a controlled before/after baseline.

Security bullet option:

- Reduced **reported high-severity container findings from 4 to 0** in local Docker Scout scans by applying OS/package security updates, pinning packaging tools and removing runtime pip.

The final image still has 1 medium and 50 low upstream findings with no reported fixes; this is not a vulnerability-free or production-security certification claim. The image audit records source, scanner, before/after reports and scope.

Optional workload bullet:

- Validated **2,018 mixed search/chat/database requests over 60 seconds with zero invalid responses** in a four-worker local test by hardening a FastAPI/PostgreSQL/Qdrant stack and verifying dependency recovery, fixture restoration and official MCP client interoperability.

## Interview walkthrough

1. Explain the uncertain-outcome problem: a client can time out after a commit and create duplicates if it retries under a new identity/key.
2. Identify the transaction boundary: receipt reservation, assessment, registry status and audit intent commit together; a failed flush rolls them back together.
3. Explain why an outbox is needed: a SQL commit and a filesystem append cannot be one database transaction. Recovery retries delivery, and event IDs prevent duplicate effects.
4. Reproduce concurrent identical requests, a changed payload, a transaction rollback and failure after ledger append. Show the raw attempt records, SQL counts, ledger/mirror counts and retained failed runs.
5. Show the explicit migration and startup verification path, bounded request admission, private operational metrics and fixture restore/recovery.
6. State what remains outside the result: external anchor custody, actual history review, independent legal evaluation, resource-dependent Langfuse validation, hosted release operation and production-scale/long-duration evidence.

## Evidence and limits

Start with [implementation index](../artifacts/reports/implementation_manifest.json), then follow its latest Docker `raw_report` to `postgres-retry-case.json`, `bounded-load.json` and `docker-tests.xml` in the same directory. The dependency audit records lock digests and scan time. The workflow is supplied for future hosted execution; no push or paid/public provisioning is implied.

Read [production design](production-design.md) for the invariants and release boundaries, and [operations runbook](operations-runbook.md) for incident/recovery procedures. These artifacts strengthen an interview explanation; they do not substitute for running the tests or operating a real deployment.
