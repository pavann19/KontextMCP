# KontextMCP

A backend reliability case study for bilingual document retrieval and permission-scoped MCP tools. Implements retry-safe PostgreSQL writes, recoverable audit delivery, migration-verified startup and bounded HTTP admission. The curated corpus is preserved; a separate official English/German publication corpus powers the hardened Docker profile.

This repository is a local engineering demo. Independent legal accuracy, general prompt-injection resistance and production operation have not been established. Real SDK clients exercise stdio and HTTP MCP; Inspector CLI also passes. Desktop UI interaction remains unverified.

## Verification status — 8 November 2026

**Locally verified:** 172 native tests and 172 Linux tests passed without failures or skips; the locked stack passed 39 integration checks. Eight-way PostgreSQL retries produced 8 assessments from 64 attempts with zero duplicate effects. Injected rollback and append-before-acknowledgement recovery preserved one ledger event and SQL mirror per committed case assessment. The 60-second four-worker workload completed 2,018 requests with zero invalid responses. Both source fingerprints match. [Docker evidence](artifacts/docker/20261108T105838Z/report.json), [dependency audit](artifacts/reports/dependency_audit.json).

Start with the [resume/interview case study](docs/resume-case-study.md), [production-oriented design](docs/production-design.md) and [operations runbook](docs/operations-runbook.md). The repository includes explicit Alembic migrations, fail-closed production configuration, HTTP body/deadline/admission limits, query-free access records and a pinned CI workflow. Hosted CI, desktop invocation, live Langfuse and external deployment/legal/custody gates remain separately scoped.

Image hardening reduced reported high-severity findings from **4 to 0** in local Docker Scout scans. The final scan has **0 critical/high, 1 medium and 50 low findings**, with no available fixes reported; residual findings remain a deployment-review gate. Python app, SDK and packaging-bootstrap advisory scans pass. Runtime pip is removed after build-time compatibility checks. [Image audit](artifacts/reports/container_image_audit.json).

Current native and locked-container validation both passed with unchanged source fingerprints; historical container evidence remains separate. See the implementation tracker below for the expanded scope and remaining external requirements.

| Area | Status | Verified evidence |
| --- | --- | --- |
| Windows regression suite | **PASS** | 172 passed, zero failed or skipped in the expanded suite. Includes real HTTP startup, authorization, writes, privacy, audit tampering and worker-process checks. [Test results](artifacts/reports/test_results.json), [source manifest](artifacts/reports/run_manifest.json). |
| Current locked local Docker | **PASS** | 39 integration checks and 172 Linux tests without skips. Retry-safe PostgreSQL writes, backup/restore, dependency recovery, real HTTP MCP and 2,018 valid mixed requests over 60 seconds. Disposable cleanup passed. [Evidence](artifacts/docker/20261108T105838Z/report.json). |
| Historical hardened local Docker integration | **PASS on earlier source** | All 31 checks passed using official snapshots, actual PostgreSQL and remote Qdrant. Includes backup restoration, dependency failure/recovery, HTTP SDK and a 60-second four-worker mixed workload: 1,514 requests, zero invalid responses. Source unchanged; disposable resources removed. [Report](artifacts/docker/20261107T041853Z/report.json). |
| Historical Linux container regression suite | **PASS on earlier source** | 138 passed, zero failed or skipped, including the separate official SDK interpreter. [Test output](artifacts/docker/20261107T041853Z/container-tests.txt). Regression fixtures are isolated; integration checks separately establish PostgreSQL/remote-Qdrant use. |
| Official Python SDK over stdio | **PASS** | SDK 2.3.0 negotiated protocol `2024-11-05`; public reads, protected-access denial and an authorized fixture write/readback passed. This was tested separately on Windows. [SDK report](artifacts/reports/mcp_sdk_interoperability.json). |
| Answer fidelity to local sources | **PASS within measured scope** | Across 225 fixed legal queries, 211 returned excerpts and all 211 matched their cited local text after configured redaction. The other 14 returned no excerpts. Expected-article relevance was 84.9%; all ten fixed unsupported cases abstained. [Answer/source report](artifacts/reports/citation_accuracy.json). |
| Retrieval comparison | **MEASURED locally** | BM25, hashed vectors, hybrid fusion and lexical reranking were measured on the generated legal-query set. This is not an independent holdout or service-capacity test. [Results and per-query samples](artifacts/reports/retrieval_ablation.json). |

The `verified/`, `historical/` and `legacy_unverified/` report directories contain older snapshots. Use the current root-level reports linked above for this status. The older reports that contained hard-coded claims remain explicitly unverified.

## Request flow

FastAPI resolves a server-owned identity, then a six-node LangGraph workflow checks input, chooses retrieval or database tools, produces an extractive response, masks recognized PII and credential patterns, and records audit metadata.

- Retrieval combines BM25 with 384-dimensional hashed lexical features stored in Qdrant. The reranker uses lexical and metadata rules; it is not a trained cross-encoder.
- Chat returns source-tagged excerpts with chunk/document identifiers and source text hashes. Its output guard rejects changed quotations, invented sources, substituted citation metadata and additional prose. Missing explicitly requested provisions produce an abstention rather than citations to unrelated chunks. These checks establish fidelity to the local corpus, not semantic entailment or legal correctness.
- Chat defaults to extractive synthesis. Optional `SYNTHESIS_MODE=ollama_select` lets Ollama select existing chunk IDs; invalid IDs or service failures fall back to deterministic selection. It cannot add generated legal claims or authorize tools.
- Database tools and the repository share application-level RBAC and department filtering. This is not database-native row-level security; trusted internal code with a raw session can bypass the repository.
- Explicit tool callers can supply `idempotency_key` to retry identical assessment fields safely; changed fields with the same caller/key are rejected. Omitting the key retains create-on-each-call behavior.
- Chat never submits compliance sign-offs. Writes require a configured compliance-officer/admin credential and explicit system ID, findings, status and finite risk score from 0 to 10 through `/api/v1/tools/call`.
- Audit logs use SHA-256 chaining, interprocess writer locking and optional HMAC checkpoints. Checkpoints are checked against the actual log prefix. Protect the signing key and retain checkpoint copies outside the writable application directory.
- New telemetry omits query text, hashes supplied session identifiers and scopes trace reads to the authenticated owner. PII pseudonym mappings are cleared when a request completes or fails.

## Local setup on Windows

Use Python 3.11 or newer (validated on Windows 3.13 and containerized Linux 3.11). Hardened deployment requires the explicit schema migration step in the [runbook](docs/operations-runbook.md); startup in production verifies the schema and does not create or adopt tables.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m app.ingestion.pipeline
# Optional: inserts demonstration enterprise records into the configured database.
.\.venv\Scripts\python.exe -m app.db.seed_data
.\.venv\Scripts\python.exe -m scripts.start_server
```

The server starts at `http://127.0.0.1:8000`; API documentation is at `/docs`. Startup creates the schema but does not automatically insert demo records.

Privileged access has no default keys. Configure `API_KEYS` in the untracked `.env` as a JSON object mapping a long random credential to `username`, `role`, and `department`. Send that credential in `X-API-Key`. Client-supplied identity and role headers cannot grant privileges in any environment. Anonymous callers have public-viewer access.

Set `AUDIT_CHECKPOINT_KEY` to a separately generated secret of at least 32 characters before creating checkpoints. After audit events exist, create a checkpoint explicitly:

```powershell
.\.venv\Scripts\python.exe -c "from app.core.audit import AuditLogger; AuditLogger.create_checkpoint()"
```

Audit verification reports failure/unavailability when its log, checkpoint ledger or signing key is absent. Existing checkpoints signed with the former source-code key are historical evidence, not trusted anchors under a newly provisioned key. Preserve old files separately and establish a reviewed new baseline; the application does not silently migrate or overwrite them.

`ALLOWED_ORIGINS` defaults to an empty list; configure explicit origins if a browser dashboard needs access. The Docker stack has passed the isolated local integration run linked above. Use `docker/compose.hardened.yml` to require provisioned credentials, run a non-root read-only application, and enable readiness and authenticated metrics. Production deployment remains unverified.

## Tests and evidence

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m scripts.generate_all_reports
.\.venv\Scripts\python.exe -m scripts.summarize_validation
```

Tests automatically create isolated temporary database, vector, telemetry and audit storage and seed their own fixtures. They do not use the configured application database. HTTP regressions exercise authentication, explicit writes, privacy, and actual application startup. Audit regressions cover truncation, rewritten chains, malformed records and concurrent worker processes.

The report generator executes pytest, saves its JUnit output, and measures retrieval over the 225 non-tool questions in the generated benchmark. Reports contain actual counts and per-query results. The five-result reranking benchmark differs from chat's three-result configuration; timings cover warm sequential local retrieval, not concurrent service capacity or model inference.

- [Current test results](artifacts/reports/test_results.json)
- [Retrieval results and individual samples](artifacts/reports/retrieval_ablation.json)
- [Answer source fidelity and fixed abstention cases](artifacts/reports/citation_accuracy.json)
- [Official SDK stdio interoperability](artifacts/reports/mcp_sdk_interoperability.json)
- [Historical unverified reports](artifacts/reports/legacy_unverified/README.md)
- [Hardening scope and limitations](docs/hardening.md)

The earlier twelve reports are retained under `legacy_unverified` because some fields were hard-coded. They must not be cited as measured evidence. Older architectural and security documents predate this hardening pass; where their claims differ, use this README, the hardening note and current generated reports.

## Implementation status and verification boundaries

| Workstream | Current evidence | Remaining boundary |
| --- | --- | --- |
| Official sources | **IMPLEMENTED / snapshot PASS**: 113 articles and 13 annexes per language, original HTML hashes and exact reparse checks. [Comparison](artifacts/reports/official_source_comparison.json). | Curated text is **not equivalent** to the official text. Human legal review remains external. Select `CORPUS_VARIANT=official` after importing. |
| Held-out evaluation | **MEASURED**: 24 frozen agent-authored questions, no fixed-benchmark overlap, 24 source-verified answers; expected article returned in 83.3%. [Results](artifacts/reports/heldout_evaluation.json). | Expectations lack independent review. An 8-case model entailment calibration scored 50%; it is unsuitable as a sole legal validator. [Calibration](artifacts/reports/entailment_calibration.json). |
| MCP clients | **IMPLEMENTED / tested**: stateless HTTP `/mcp`, real SDK stdio/HTTP tests, [Inspector CLI PASS](artifacts/reports/inspector_validation.json), VS Code workspace configuration. | Actual desktop UI invocation remains blocked by unreliable native-dialog input targeting. [Attempt](artifacts/reports/desktop_mcp_validation.json). |
| Deployment operations | **IMPLEMENTED**: hardened local Docker, readiness, private metrics, fixture backup/restore, database/vector outage recovery and bounded mixed-load runner. | Earlier container verification passed 138 Linux tests and the bounded workload. Fresh locked-image validation passed 39 integration checks and 172 Linux tests; fixture restore, recovery and the bounded workload passed. No cloud, production capacity or long-duration soak claim. |
| Production design and release | **IMPLEMENTED / locally tested**: explicit migrations and drift checks, fail-closed configuration, bounded admission, query-free access records, deployment/incident runbook and locked dependency audit. [Design](docs/production-design.md). | CI workflow is supplied and locally checked; hosted execution, TLS/ingress, independent backups/keys, OS-image scanning, production soak and release operation require deployment evidence. |
| Atomic audit delivery | **IMPLEMENTED / tests PASS**: assessment and outbox intent commit together; retries deduplicate file delivery and repair SQL mirror after interruption. | Operate and monitor the dispatcher; file/SQL delivery is eventual. |
| External audit anchors | **IMPLEMENTED / fixture tests PASS**: Ed25519 signed exports, independently pinned public-key verification and tamper checks. | Operator must retain keys and anchors outside application custody. |
| Expanded defenses | **MEASURED**: 120 generated attacks, 24 benign controls, 40 email cases; no unexpected writes or known private-marker leaks. [Results](artifacts/reports/expanded_defense_evaluation.json). | Guard block rate was 90%; finite cases do not establish universal resistance or arbitrary PII detection. |
| Historical retention | **IMPLEMENTED / fixture tests PASS**: inventory, encrypted quarantine, restore, tamper rejection and manifest-gated deletion. [Inventory](artifacts/reports/retention_inventory.json). | Existing user history is preserved pending review; no automatic deletion was performed. |
| Ollama / Langfuse | **Ollama PASS**: actual isolated generation, loaded-model proof and guarded source selection. [Evidence](artifacts/reports/ollama_validation.json). Langfuse upstream configuration and exporter validation implemented. | Langfuse live ingestion/readback is **BLOCKED_RESOURCE**; no stack was started. [Report](artifacts/reports/langfuse_validation.json). |

See [implementation checklist](docs/implementation-checklist.md) for reproduction commands and scope, and the [implementation evidence index](artifacts/reports/implementation_manifest.json) for hashed report links. Historical results retain their original source boundary.

Raw internal database sessions can bypass application-level repository filtering. Extractive answers can faithfully reproduce irrelevant or inaccurate curated text. No claim of database-native row-level security, trained semantic embeddings, a trained cross-encoder, legal correctness or production readiness is made.

## Stdio tool transport

Run `python -m scripts.start_mcp` from the repository directory. The adapter accepts line-delimited JSON-RPC on stdin and reserves stdout for responses. Set `MCP_API_KEY` to a credential provisioned in `API_KEYS` for privileged tools. Without it, the adapter uses public-viewer access. Local subprocess checks cover initialization, notifications, listing, reads and parse errors. The independent SDK check below also passes over stdio; HTTP MCP compatibility is also covered by a real SDK client; desktop UI compatibility remains unverified.

## Independent SDK check

The SDK client uses its own environment so its dependency versions do not change the application environment:

```powershell
python -m venv .venv-mcp-sdk
.\.venv-mcp-sdk\Scripts\python.exe -m pip install -r requirements-mcp-client.txt
.\.venv\Scripts\python.exe -m pytest tests/mcp/test_official_sdk.py -q
```

Set `MCP_SDK_PYTHON` when the client environment is elsewhere. Without this interpreter, the SDK test is skipped and its report remains unverified. The test runs against automatically isolated fixtures; it never uses the application database. See the [official SDK transport documentation](https://py.sdk.modelcontextprotocol.io/client/transports/).

Chat responses include `grounding_status`: `SOURCE_VERIFIED` means the returned, redacted excerpts and citation metadata match loaded local chunks; `REJECTED` means the output check removed an invalid answer; `NOT_APPLICABLE` covers notices, abstentions and tool-only formatting. Tool results are not marked as legally source-verified.

## Local Docker verification

The core FastAPI/PostgreSQL/Qdrant stack passed isolated Docker checks, including restart persistence and signed audit verification. See [Docker validation](docs/docker-validation.md) for fixes, test results, limits and reproduction instructions. Ollama has separate live evidence; Langfuse live operation and production capacity remain unverified.

## Reproduce isolated Docker verification

```powershell
.\.venv\Scripts\python.exe -m scripts.validate_docker
```

This builds and starts a disposable project using the validation Compose override, seeds only that project, exercises PostgreSQL and remote Qdrant, runs the Linux regression suite, and records timestamped evidence under `artifacts/docker/`. The script removes its project resources afterward. This is a local integration check, not a cloud deployment or production load test. Historical failed attempts remain alongside the successful run for provenance.
