# Operations and release runbook

## Fresh local hardened deployment

Run from the repository root. Supply random `KONTEXT_POSTGRES_PASSWORD`, `AUDIT_CHECKPOINT_KEY` and the server-owned `API_KEYS` mapping through the deployment environment. Keep credentials out of shell history, screenshots, Git and reports. Preserve the data volumes; never use `down --volumes` on a real deployment.

```powershell
docker compose -f docker/docker-compose.yml -f docker/compose.hardened.yml build app
docker compose -f docker/docker-compose.yml -f docker/compose.hardened.yml up -d --wait postgres qdrant
docker compose -f docker/docker-compose.yml -f docker/compose.hardened.yml run --rm --no-deps app python -m scripts.migrate_db upgrade
docker compose -f docker/docker-compose.yml -f docker/compose.hardened.yml up -d --wait app
```

These commands are for a fresh, dedicated deployment. Existing unversioned databases require the reviewed adoption procedure in [production design](production-design.md), rehearsed on a copy. Schema verification refuses to silently migrate or adopt user history. The base profile publishes only localhost ports; configure a reviewed TLS/host/network override before any remote exposure. Starting a server does not seed demo enterprise records.

## Readiness fails

Inspect the database/vector service health and sanitized application logs. Check disk space and memory, then run `scripts.migrate_db check` through the application image. A missing revision or schema drift is a release failure: do not switch to schema creation mode in production. Restore dependency availability and confirm readiness before sending business traffic. `/health` alone proves only that the process can respond.

## Write times out

The commit outcome may be uncertain. Retry identical business fields with the original idempotency key under the same provisioned identity. Do not generate a new key just because the client timed out. Read the returned assessment and current registry status; an old retry must not reverse newer business state. A changed payload must use a deliberate new operation/key after review, not overwrite the previous receipt.

## Audit backlog grows

Use authorized metrics to inspect pending count, oldest pending age and failed delivery attempts. A value of -1 means unknown storage state. Check database connectivity, ledger path availability, permissions, disk headroom and the outbox worker. Do not delete pending rows, reset the ledger or bypass signature failures. Committed intent survives delivery failure; retry after the underlying cause is repaired. Verify the ledger chain and delivery receipts after recovery. Audit tampering requires incident review and independently held anchor verification.

## Requests are rejected

413 means the body exceeds the configured limit; 408 means upload exceeded the body deadline; 503 with Retry-After means admission is saturated. Retry with bounded exponential backoff and jitter. Retain idempotency keys for writes. Check CPU, disk, database pressure and request duration before increasing limits. The application limit is per process; deployment ingress must handle per-client and distributed abuse controls. Do not use retries to evade host/identity rejection.

## Backup and rollback

Schedule encrypted PostgreSQL dumps plus ledger/checkpoint/anchor backups to independently controlled storage. Record schema/image/corpus identities alongside each backup. A successful dump alone is insufficient: restore into a separate database and verify business counts, schema, receipts and ledger integrity. Protect decryption/signing keys separately and rehearse access without the application host.

For a failed release, stop new traffic, assess uncertain writes and preserve diagnostics. Roll back to a compatible image or restore a verified snapshot to separate resources before an operator-controlled cutover. Never downgrade the baseline migration to drop business/audit tables. Destructive history disposition requires a reviewed unchanged retention manifest and explicit operator handling.

## Release review

- Native report and Docker report pass on the exact source; Linux JUnit is present, parsed and has no failures/skips.
- The locked image's resolved dependencies match the lock; app/SDK/bootstrap Python advisory scans are current and passing. The image scan has no high/critical or fixable findings; unfixed medium/low findings are reviewed and accepted by the deployment owner.
- Migration, retry/fault case, restore, dependency recovery, SDK and bounded load checks pass; fixture cleanup is confirmed.
- Deployment TLS, host policy, credentials/rotation, backup custody, monitoring, ownership and incident handling are configured and rehearsed.
- A representative longer soak and workload-specific objectives are reviewed before claiming capacity or an SLA.

The first three are locally reproducible portfolio evidence. Hosted CI status, managed production operation and the deployment-owner checks require separate evidence. Optional Langfuse needs a sufficiently resourced endpoint; synthetic trace acceptance and readback must pass before claiming live remote observability.


The hardened runtime intentionally has no pip in either interpreter. Dependency compatibility is checked at image build and retained as `/opt/kontext-build/app-pip-check.txt` and `sdk-pip-check.txt`; validation verifies those files and pip absence. Update dependencies by rebuilding/revalidating the image, not by installing into running containers. Review `artifacts/reports/container_image_audit.json` and its raw SARIF before release.

## Reproduce Python advisory checks

```powershell
python -m venv .venv-audit
.\.venv-audit\Scripts\python.exe -m pip install -r requirements-audit.txt
$env:KONTEXT_AUDIT_PYTHON = (Resolve-Path .\.venv-audit\Scripts\python.exe).Path
.\.venv\Scripts\python.exe -m scripts.audit_dependencies
.\.venv\Scripts\python.exe -m scripts.summarize_validation
```

For the image scan, select the exact image recorded in the current Docker run's `images.txt`, run Docker Scout against that local image and retain the raw SARIF plus image ID. A scanner exit code of zero may only mean the report was produced; inspect severity and fix availability explicitly. The current snapshot has no critical/high or fixable findings but retains unfixed medium/low entries. Repeat the scan before release because advisory data changes.
