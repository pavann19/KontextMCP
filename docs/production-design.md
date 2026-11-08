# Production-oriented portfolio design

KontextMCP is a local-validated backend case study. The deployment design has production safeguards, but no production users, managed SLA, high availability or independent legal approval are claimed. The strongest evidence is retry-safe state mutation, recoverable audit delivery and reproducible fault checks.

## Boundaries and invariants

| Boundary | Enforced behavior | Evidence |
| --- | --- | --- |
| HTTP admission | One-MiB bodies, five-second total body deadline, sixteen active requests per process; overload returns 503 with Retry-After | Streaming/understated-body, slow-client, overload, cancellation and liveness tests |
| Caller identity | Only server-configured API credentials assign roles and departments; a role header cannot elevate access | REST, SDK stdio/HTTP and repository tests |
| Assessment commit | Retry receipt, assessment, registry status and audit intent commit together; changed payloads cannot reuse a key | Concurrent/rollback tests and disposable PostgreSQL case study |
| Audit delivery | Event IDs deduplicate a durable, locked, hash-chained ledger; SQL mirror and acknowledgement recover after interruption | Outbox fault checks and signature/checkpoint tests |
| Legal text | Output matches the cited local source or is removed; missing named provisions abstain | Source-fidelity and unsupported-query cases; independent relevance/legal review remains separate |
| Schema deployment | Explicit Alembic migrations precede application startup; verify mode refuses missing revisions and drift | Fresh upgrade, additive-index evolution, data preservation and legacy refusal tests |

The admission limit is per process, not a distributed rate limit. The hardened image uses one Uvicorn worker with an additional 64-connection concurrency bound. Liveness remains accessible under application overload; readiness still performs dependency checks and may be rejected during overload. Request deadlines bound body upload, not a committed database operation. Clients must retain idempotency keys and handle uncertain outcomes by replay/readback.

## Deployment shape

The supported local profile is one application instance, PostgreSQL, remote Qdrant and a dedicated writable audit/data volume. The app runs as an unprivileged user with a read-only root, dropped capabilities, no-new-privileges, memory/CPU/process limits and bounded log rotation. Secrets are supplied at deployment, never baked into images. Startup rejects debug mode, disabled guards, missing/short credentials, default database passwords, local-vector fallback, wildcard hosts/origins and implicit schema creation in production mode.

Internet-facing deployment additionally needs a TLS-terminating ingress with connection/per-client limits, trusted-proxy configuration, secret management and rotation, network policy and monitoring. Those are deployment prerequisites, not claims established by localhost tests. Do not expose database/vector ports publicly. The repository does not supply authentication federation, database-native tenant row security or multi-region failover.

## Data and release lifecycle

1. Back up PostgreSQL, the audit ledger/checkpoints and the independently pinned anchor material. Record the image digest, corpus digest and schema revision.
2. Apply the reviewed migrations once through `python -m scripts.migrate_db upgrade`; PostgreSQL migrators serialize on an advisory transaction lock.
3. Start the application in `DATABASE_SCHEMA_MODE=verify`. Readiness gates database/vector availability. A drifted or unversioned database must not be silently adopted.
4. Verify a disposable credential/read/write, ledger integrity, outbox backlog and fixture restore before rollout. No automatic destructive schema downgrade is provided.
5. Roll back only to an image compatible with the current schema. Otherwise restore a reviewed backup to separate storage, verify it, and perform an operator-controlled cutover.

The baseline is frozen migration code, not a live import of ORM table definitions. Revision 0002 adds an outbox delivery/creation index. Existing unversioned databases are preserved: take a backup, compare their schema/data with the baseline and rehearse adoption on a copy before an operator explicitly stamps a reviewed revision. Do not run fresh-baseline DDL or blind stamping against historical user data.

The default development mode still creates isolated/demo schemas. Normal server startup no longer inserts sample business records. Use `python -m app.db.seed_data` only when demonstration records are explicitly wanted.

## Operational model

`/health` is liveness; `/ready` checks dependencies, not legal correctness or audit completeness. Authorized `/metrics` exposes HTTP errors, duration sum, outbox count/age/failures/attempts and fixed admission-rejection categories. Unknown outbox storage state is -1 and must alert. Metrics and admission accounting are process-local; PostgreSQL stores durable outbox state.

Access records contain generated request IDs, method, matched route template, response status and duration. Query strings, body text, credential headers and raw unmatched paths are omitted. The hardened launcher disables Uvicorn's default query-bearing access log. Keep infrastructure/proxy logging subject to the same privacy policy. Explicit benchmark execution is disabled on production request paths; GET endpoints never launch missing evaluations.

Alerts to configure at deployment: sustained readiness failure; 5xx increase; overload rejection; any failed outbox delivery; oldest pending age beyond the team's delivery objective; disk/headroom exhaustion; backup/anchor verification failure. Availability, latency, recovery and retention objectives require workload and owner agreement. This portfolio does not invent an SLA or production RPO/RTO from a short fixture run.

## Reproducibility and remaining gates

The immutable-image/version-lock validation builds a new image, migrates a fresh database, runs a synthetic PostgreSQL retry/fault case, exercises API/SDK and recovery behavior, performs bounded mixed load, and parses the Linux JUnit artifact before accepting success. The workflow in `.github/workflows/validation.yml` pins action revisions and uses read-only repository permissions. Its hosted execution is unverified until pushed and run with approval; local-equivalent commands are executed separately.

Known Python dependency advisories are checked by an isolated pip-audit environment against both complete version locks. Passing means no known findings at scan time, not universal vulnerability absence. The local image scan is recorded separately, including residual unfixed advisories. Signed publication/SBOM attestation and hosted release operations remain deployment work.

Langfuse is optional for business correctness. Its full local stack remains blocked by the four-GiB Docker memory allowance; a configured endpoint and resources are needed for live ingestion/readback. Desktop UI invocation, independently controlled anchors, reviewed disposition of actual user history, independent legal evaluation and long-running production operation remain external gates.


## Verified portfolio release, 8 November 2026

The [final Docker run](../artifacts/docker/20261108T105838Z/report.json) passed 39 integration checks and 172 Linux tests without skips; the native suite passed the same 172 tests. Its PostgreSQL case collapsed 64 retry attempts at eight-way concurrency into 8 assessments with zero duplicate effects, rejected 8 payload conflicts and recovered the injected delivery fault for 10 case assessments. The four-worker mixed workload completed 2,018 requests in 60 seconds with zero invalid responses. Fixture cleanup passed. The app and SDK dependency sets passed build-time `pip check` before pip was removed from both runtime interpreters, and the version-lock advisory scan reports no known findings at scan time. These are local results, not production capacity or hosted-CI claims.


Image hardening applied Debian security upgrades, removed runtime build compilers, pinned packaging bootstrap tools in both interpreters and upgraded Mako to 1.4.3. The same local Docker Scout version reported 142 findings (4 high) before remediation and 51 findings (0 critical/high, 1 medium, 50 low) afterward. No remaining finding has a reported fix. The medium GNU tar issue is reported as disputed/upstream behavior; the HTTP service does not extract submitted archives, but this observation is not independent risk acceptance or a reason to hide the finding. Residual advisories require deployment-owner review. The raw SARIF snapshots remain preserved.


Evidence files covered by `.gitattributes` retain exact bytes in Git so Windows line-ending conversion cannot break recorded report hashes. Release review checks staged report blobs as well as working files. Source fingerprints describe the observed workspace bytes; a checkout with different source line endings requires fresh validation rather than pretending the historical byte fingerprint is current.
