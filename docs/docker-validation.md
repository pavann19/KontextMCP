# Hardened local Docker validation

Current follow-up status: **PASS**. The 8 November locked-image run passed all 39 integration checks and all 172 Linux regression tests without skips. PostgreSQL retry-safe writes/conflicts, audit health metrics, backup/restore, dependency recovery, real HTTP MCP and bounded load passed. Source remained unchanged and disposable-project cleanup passed. [Current timestamped evidence](../artifacts/docker/20261108T105838Z/report.json). Earlier storage and startup failures are preserved as historical attempts.

The current run used official English/German publication snapshots, FastAPI, actual PostgreSQL and remote Qdrant. See the [current indexed report](../artifacts/reports/docker_validation.json). The [7 November run](../artifacts/docker/20261107T041853Z/report.json) remains historical evidence for its earlier source.

## Deployment behavior

The application runs as user 10001 with a read-only root filesystem, dropped capabilities, no-new-privileges, bounded resources and a dedicated writable data volume. Hardened Compose requires random database credentials, API credentials and an audit checkpoint secret. It does not mount historical host runtime records.

`/ready` checks actual database/vector availability; `/metrics` requires an authorized credential. Audit intent is committed with the assessment and delivered by the retrying outbox worker. Explicit provision requests use trusted metadata so cross-references elsewhere in the full official text cannot displace a named article.

## Validation scope

The disposable runner checks packaging exclusions, authentication and department boundaries, schema rejection, explicit database writes/readback, unique IDs, remote vector retrieval, trace privacy, application restart persistence and signed audit verification. It also restores a fixture PostgreSQL dump into a separate database, compares assessment counts, stops/restarts only its own database and vector dependencies, and checks readiness failure/recovery. A real independent SDK negotiates Streamable HTTP MCP.

The bounded workload mixes search, chat and authorized database reads for 60 seconds with four workers. The current run completed 2,018 requests with zero invalid responses. This is a short correctness check under concurrency, not a production-capacity or long-duration soak claim. Raw responses are represented by operation, status, validation result and latency; user inputs/credentials are not logged.

All 39 integration checks and all 172 Linux regression tests passed without skips. The source fingerprint stayed unchanged. Cleanup passed and removed the disposable project resources. Earlier failed attempts are preserved, including a missing Docker engine, a direct-script import issue and an official-corpus retrieval abstention exposed by the workload. The retrieval issue has a dedicated regression test. Only project-scoped disposable resources are removed; unrelated running services and existing application records are preserved.

## Reproduce

With Docker running and both the application and separate MCP SDK environments installed:

```powershell
.\.venv\Scripts\python.exe -m scripts.validate_docker
```

The runner combines base, validation and hardened Compose files with a unique project name and disposable volumes, saves timestamped evidence under `artifacts/docker/`, then removes its resources. To run persistent hardened local services, combine the base and hardened files and supply the required secrets; keep the dedicated volume and back it up. No code, image or cloud resources are published.

Real Ollama generation has separate native evidence. Langfuse uses a separately preserved official multi-service stack and remains blocked by its local memory requirement. Actual desktop UI invocation, independent legal review, external key custody and production operation remain outside this container result.


The current runner migrates a fresh PostgreSQL schema before application startup, then runs the synthetic retry/fault case without a competing application worker. Production startup verifies migration head and schema drift. The case report records individual acknowledged attempts and separately labels a simulated discarded acknowledgement; it is not a real-network-loss claim. Admission rejects oversized REST bodies before handlers, while unit regressions exercise chunked/understated lengths, slow bodies, saturation and cancellation. See `postgres-retry-case.json` alongside the current raw report.
