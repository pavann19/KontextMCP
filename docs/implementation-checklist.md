# Remaining-scope implementation tracker

User authorization: implement the README pending items; use suitable project defaults. Target: hardened local Docker, no paid/public cloud provisioning. Preserve existing runtime data and frozen evidence.

| Workstream | Implementation | Required evidence |
| --- | --- | --- |
| Official sources | English/German EUR-Lex snapshots and separate official corpus importer; preserve curated baseline | Reparse/hash comparison, full article/annex coverage; human legal review remains external |
| Evaluation | Frozen disjoint question set, answer relevance and optional model entailment evaluator | Raw per-case results, dataset digest and model provenance; no human/legal accuracy claim |
| MCP clients | Stateless HTTP + SDK/Inspector checks; VS Code configuration | Real HTTP client lifecycle, authorization, read/write; desktop UI result separately scoped |
| Deployment operations | Readiness, authenticated metrics, hardened Compose, bounded load, backup/restore and dependency outage recovery | Disposable-project raw reports and cleanup |
| Atomic audit intent | Business record + outbox in one DB transaction, retry/deduplication dispatcher | Rollback, unavailable ledger and crash-after-append tests |
| External anchors | Ed25519 export and pinned-public-key verification outside data directory | Restore, rewrite/truncation and forged-key tests; external storage custody separate |
| Defense coverage | Generated adversarial/property cases with benign controls | Raw failures/false positives; never claim universal resistance |
| Retention | Inventory and encrypted quarantine/export + reviewed deletion workflow | Fixtures round-trip and tamper rejection; do not delete user history automatically |
| Optional services | Real Ollama source-selection mode and Langfuse deployment/export validation | Actual generation + loaded model and accepted/retrieved trace, or explicit resource/access blocker |

## Evidence on 8 November 2026

Current native and Linux suites each passed **172 tests, zero failures and zero skips**. The locked [20261108T105838Z run](../artifacts/docker/20261108T105838Z/report.json) passed 39 integration checks: explicit schema migration, 64 concurrent retry attempts at eight-way concurrency yielding 8 assessments, rollback/delivery-fault recovery, fixture backup/restore, dependency recovery and real HTTP MCP. A 60-second four-worker workload completed 2,018 requests with zero invalid responses. Source fingerprints and fixture cleanup passed. Earlier runs retain their own historical scope.

Production configuration/admission/schema tests and the known-advisory audit passed. See [design](production-design.md), [operations runbook](operations-runbook.md) and [resume evidence](resume-case-study.md). The CI workflow is implemented but hosted execution remains unverified; external desktop invocation remains BLOCKED_UI_AUTOMATION.

- Official snapshots: `artifacts/reports/official_source_comparison.json`; 113 articles and 13 annexes in each language. Curated equivalence fails honestly; the official corpus is separate.
- Frozen holdout: `heldout_evaluation.json`; 24 queries, 83.3% expected-article relevance. Model calibration: `entailment_calibration.json`; 50% over eight cases, unsuitable as sole legal validator.
- Actual independent clients: `inspector_validation.json`, SDK stdio report and real HTTP SDK tests. VS Code configuration is supplied; its desktop UI remains unverified.
- Audit outbox, external anchor and retention fixture cases are included in the native suite. User history remains preserved.
- `expanded_defense_evaluation.json`: 120 attacks, 24 benign controls and 40 email cases. No universal security claim.
- `ollama_validation.json`: actual generation and guarded source selection passed. `langfuse_validation.json`: live deployment blocked by its local memory requirement; upstream stack snapshot saved.

See [8 November gap follow-up](gap-closure-2026-11-08.md) for bounded CLI execution and source-checked evidence indexing.

## Reproduce

Run commands from the repository root, using the application environment:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m scripts.generate_all_reports
.\.venv\Scripts\python.exe -m scripts.import_official_corpus
.\.venv\Scripts\python.exe -m scripts.evaluate_holdout
.\.venv\Scripts\python.exe -m scripts.evaluate_defenses
.\.venv\Scripts\python.exe -m scripts.validate_inspector
.\.venv\Scripts\python.exe -m scripts.validate_ollama
.\.venv\Scripts\python.exe -m scripts.validate_langfuse
.\.venv\Scripts\python.exe -m scripts.validate_docker
.\.venv\Scripts\python.exe -m scripts.manage_retention inventory
```

Official import requires network access and produces a new content-addressed snapshot. Inspector requires Node/npm access. Ollama validation starts and closes its own isolated server. Docker validation uses only its unique disposable project, including a fixture database backup and restore, dependency outages and a 60-second concurrent mixed workload. The SDK uses a separate interpreter configured by `MCP_SDK_PYTHON`.

Use `scripts.audit_anchor --help` to establish separately held signing material and verify signed exports against a pinned public key. Use `scripts.manage_retention --help` for encrypted quarantine and restore. Deletion requires a reviewed unchanged manifest and explicit confirmation; this task has not deleted existing history.

## External requirements

Independent legal review, desktop UI invocation, protected external anchor custody, reviewed history disposition, long-duration production validation and live Langfuse ingestion/readback remain incomplete. These cannot be inferred from fixture tests or an upstream configuration file. No public or paid deployment was provisioned.
