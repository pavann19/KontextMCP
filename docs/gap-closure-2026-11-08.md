# Gap follow-up: 8 November 2026

## Closed in code

Docker commands now write output to temporary files and wait only for their own CLI process. A timed-out child cannot hold a capture pipe open indefinitely. The timeout result preserves output, returns exit code 124 and states that only the CLI was stopped; a missing executable returns 127. This does not imply that a background Docker build or service was cancelled.

Docker validation checks engine access before creating fixture resources. An unavailable engine produces a saved `BLOCKED_DOCKER` report with `cleanup: NOT_REQUIRED`. Optional Langfuse validation uses the same bounded engine check and reports unknown memory as null.

`python -m scripts.summarize_validation` refreshes report hashes and checks the native source fingerprint. It indexes the latest Docker attempt separately from the historical successful run and rejects a passing Docker report whose source fingerprint is stale. Run it after generating native and Docker reports.

## Current verification boundaries

The final native run passed 150 tests with zero failures or skips and an unchanged source fingerprint. Every report hash in the refreshed implementation index matches its file. New regression cases exercise inherited output handles, retained failure output and Docker rejection before resource creation.

Docker access was restored after the earlier startup socket conflict. The fresh locked-image run passed 34 integration checks and 150 Linux tests without skips. Retry-safe PostgreSQL writes, backup/restore, database/vector recovery, signed audit persistence and real HTTP MCP passed. A 60-second four-worker mixed workload completed 2,164 requests with zero invalid responses; source remained unchanged and disposable-project cleanup passed. [Current evidence](../artifacts/docker/20261108T052607Z/report.json). Earlier failed attempts remain preserved; no factory reset, disk repair or shared-volume removal was performed.

VS Code 1.145.2 opened the correct project and exposed its accessibility tree. Desktop input did not reliably reach the intended command controls; tool discovery and invocation remain unverified. No privileged credential was entered and no desktop MCP server was started.

Langfuse ingestion/readback remains blocked by its local memory requirement: the current engine exposes about four GiB, below the saved upstream recommendation. No optional service was provisioned. Independent legal review, external anchor custody, reviewed disposition of actual history, and production soak/capacity evidence remain external requirements.

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m scripts.generate_all_reports
.\.venv\Scripts\python.exe -m scripts.validate_docker
.\.venv\Scripts\python.exe -m scripts.validate_langfuse
.\.venv\Scripts\python.exe -m scripts.summarize_validation
```

The first command uses isolated local fixtures. Docker validation uses only its uniquely named disposable project when the engine is available. Reports retain failures and blockers; CLI/SDK tests do not establish desktop UI, legal approval or production readiness.


## Container evidence capture

The first restored-engine attempt passed the runtime checks but its best-effort Docker copy could not retrieve the JUnit file from the container tmpfs. Its raw report and copy error remain preserved under `artifacts/docker/20261108T051848Z/`. The validator now reads XML through container exec and requires nonempty, parsed evidence with zero failures or skips before recording the Linux suite as passed. The final run `20261108T052607Z` contains the verified XML. Its installed Python package versions exactly match `requirements-linux.lock`; both current source fingerprints and all indexed report hashes match.


## Later production-oriented portfolio release

The current [20261108T103840Z run](../artifacts/docker/20261108T103840Z/report.json) supersedes the earlier local source: 37 integration checks, 172 Linux tests, 172 native tests and 2,072 valid mixed requests in 60 seconds. Explicit schema migration/drift checks, fail-closed production settings, HTTP admission and the PostgreSQL retry/fault case passed. Historical attempts above remain preserved. See [production design](production-design.md), [operations](operations-runbook.md) and [resume evidence](resume-case-study.md).


## Final image-security follow-up

The current source is verified by [20261108T105838Z](../artifacts/docker/20261108T105838Z/report.json): 39 integration checks, 172 Linux tests, 172 native tests and 2,018 valid mixed requests over 60 seconds. Mako is now pinned to 1.4.3 in the image, packaging bootstrap tools are version-locked, Debian security updates are applied, runtime build compilers are omitted and pip is removed after build-time dependency checks. Local Scout reports 0 high/critical findings, down from 4 high before remediation, with 1 medium and 50 low unfixed findings retained for review. Earlier phase counts and scans remain historical.
