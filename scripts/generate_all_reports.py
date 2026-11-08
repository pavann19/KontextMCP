"""Generate measured local evidence, preserving previous reports as unverified history.

Runs the test suite against isolated fixtures. Retrieval measurements use in-memory
Qdrant and read the curated corpus without modifying application data.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REPORT_NAMES = (
    "authorization_report", "audit_integrity", "agent_reliability", "citation_accuracy",
    "legal_corpus_validation", "test_results", "retrieval_benchmark", "retrieval_ablation",
    "prompt_injection_report", "privacy_verification", "performance_benchmark", "mcp_reliability", "mcp_sdk_interoperability"
)


def write_report(directory, name, data):
    payload = {"timestamp": datetime.now(timezone.utc).isoformat(), "scope": "local", **data}
    (directory / (name + ".json")).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_test_reports(directory):
    junit = directory / "hardening-tests.xml"
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q", "--tb=short", "--disable-warnings", "--junitxml=" + str(junit)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "MCP_SDK_REPORT_PATH": str(directory / "mcp_sdk_interoperability.json")}
    )
    (directory / "pytest-output.txt").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    cases = list(ET.parse(junit).getroot().iter("testcase")) if junit.exists() else []

    def summarize(selected):
        failures = sum(c.find("failure") is not None for c in selected)
        errors = sum(c.find("error") is not None for c in selected)
        skipped = sum(c.find("skipped") is not None for c in selected)
        return {
            "status": "FAIL" if failures or errors else ("PASS" if selected and len(selected) > skipped else "UNVERIFIED"),
            "collected": len(selected), "passed": len(selected) - failures - errors - skipped,
            "failed": failures, "errors": errors, "skipped": skipped,
            "test_ids": [c.get("classname", "") + "." + c.get("name", "") for c in selected],
            "evidence": "hardening-tests.xml", "limitation": "Automated local checks only; no production or general security guarantee."
        }
    summary = summarize(cases)
    summary["exit_code"] = completed.returncode
    if completed.returncode:
        summary["status"] = "FAIL"
    write_report(directory, "test_results", summary)
    groups = {
        "authorization_report": ("permissions", "cross_department", "tool_authorization", "hardening_http"),
        "audit_integrity": ("audit",),
        "agent_reliability": ("agent",),
        "legal_corpus_validation": ("legal",),
        "prompt_injection_report": ("injection", "red_teaming"),
        "privacy_verification": ("pii", "privacy", "session_isolation", "hardening_http"),
        "mcp_reliability": ("mcp",),
    }
    for name, patterns in groups.items():
        result = summarize([c for c in cases if any(p in c.get("classname", "") for p in patterns)])
        if name == "legal_corpus_validation":
            result["official_source_equivalence"] = "UNVERIFIED"
            result["limitation"] = "Checks local curated data and official snapshot reparse consistency; separate official_source_comparison.json reports curated differences. No independent legal review."
        if name == "mcp_reliability":
            result["limitation"] = "Dispatcher, subprocess and real HTTP SDK checks. See mcp_sdk_interoperability.json and inspector_validation.json for independent client evidence; desktop UI invocation remains unverified."
        write_report(directory, name, result)
    return completed.returncode


def run_retrieval_reports(directory):
    from app.ingestion.pipeline import IngestionPipeline
    from app.retrieval.bm25 import BilingualBM25Retriever
    from app.retrieval.dense import DenseRetriever
    from app.retrieval.hybrid import HybridRetriever
    from app.retrieval.reranker import LegalCrossReranker
    from app.evaluation.benchmark_dataset import generate_benchmark_dataset
    from app.evaluation.evaluator import BenchmarkEvaluator
    from app.config import settings
    settings.QDRANT_PREFER_LOCAL = False
    settings.QDRANT_HOST = None
    chunks = IngestionPipeline().load_cached_chunks()
    bm25, dense = BilingualBM25Retriever(), DenseRetriever(storage_path=None)
    try:
        bm25.index(chunks)
        dense.index(chunks)
        hybrid = HybridRetriever(bm25=bm25, dense=dense)
        reranker = LegalCrossReranker(top_n=5)
        dataset = [q for q in generate_benchmark_dataset() if q.language != "tool"]
        configs = {
            "bm25": lambda q, lang: bm25.search(q, top_k=5, language=lang),
            "hashed_vectors": lambda q, lang: dense.search(q, top_k=5, language=lang),
            "hybrid_rrf": lambda q, lang: hybrid.search_rrf(q, top_k=5, language=lang),
            "lexical_reranked_top5": lambda q, lang: reranker.rerank(q, hybrid.search(q, top_k=10, language=lang), top_n=5, target_language=lang),
        }
        import numpy as np
        results, samples = {}, {}
        for name, search in configs.items():
            rows = []
            for item in dataset:
                lang = item.language if item.language in {"en", "de"} else None
                start = time.perf_counter()
                hits = search(item.query, lang)
                latency = (time.perf_counter() - start) * 1000
                rank = next((i for i, (chunk, _) in enumerate(hits, 1)
                             if BenchmarkEvaluator._matches_expected_article(chunk.article_id, item.expected_article_id)), 0)
                rows.append({"query_id": item.query_id, "language": item.language, "expected_article": item.expected_article_id, "rank": rank,
                             "latency_ms": latency, "retrieved_articles": [c.article_id for c, _ in hits]})
            def metrics(subset):
                return {**{f"hit_at_{k}": sum(0 < r["rank"] <= k for r in subset) / len(subset) for k in (1, 3, 5)},
                        "mrr": sum(1/r["rank"] if r["rank"] else 0 for r in subset) / len(subset),
                        "queries": len(subset), "mean_latency_ms": float(np.mean([r["latency_ms"] for r in subset])),
                        "p95_latency_ms": float(np.percentile([r["latency_ms"] for r in subset], 95))}
            results[name] = {"overall": metrics(rows), "by_language": {
                lang: metrics([r for r in rows if r["language"] == lang]) for lang in sorted({r["language"] for r in rows})}}
            samples[name] = rows
        details = {"status": "PASS", "evaluation_queries": len(dataset), "excluded": "Tool queries are not retrieval tasks.",
                   "limitation": "Fixed generated queries over a curated corpus, no independent holdout. Warm sequential retrieval only. Reranked benchmark returns five candidates; chat returns three.",
                   "configurations": results, "samples": samples}
        write_report(directory, "retrieval_ablation", details)
        write_report(directory, "retrieval_benchmark", {k:v for k,v in details.items() if k != "samples"})
        write_report(directory, "performance_benchmark", {
            "status": "PASS", "scope": "local retrieval only", "configurations": {k:v["overall"] for k,v in results.items()},
            "agent_latency": "UNVERIFIED", "throughput": "UNVERIFIED",
            "limitation": "No network, model inference, concurrent load, or production capacity measurement."
        })
    finally:
        dense.client.close()


def source_digest():
    digest = hashlib.sha256()
    for path in sorted([*ROOT.glob("app/**/*.py"), *ROOT.glob("tests/**/*.py"),
                        *ROOT.glob("migrations/**/*.py"), *ROOT.glob(".github/workflows/*"),
                        *ROOT.glob("scripts/*.py"), *ROOT.glob("requirements*.txt"), *ROOT.glob("requirements*.lock"),
                        *ROOT.glob("data/raw/*.json"), *ROOT.glob("data/chunks/*.json"),
                        *ROOT.glob("data/official/*.json"), *ROOT.glob("data/evaluation/*")]):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts" / "reports")
    args = parser.parse_args()
    directory = args.output_dir.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    # Keep the previous unverified artifacts available for provenance.
    archive = directory / "legacy_unverified"
    if not archive.exists():
        archive.mkdir()
        for name in REPORT_NAMES:
            source = directory / (name + ".json")
            if source.exists():
                shutil.copy2(source, archive / source.name)
        (archive / "README.md").write_text("Historical reports retained for provenance. These contain hard-coded or otherwise unverified claims and must not be used as measured evidence.\n", encoding="utf-8")
    history = directory / "historical" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    history.mkdir(parents=True)
    for name in REPORT_NAMES:
        source = directory / (name + ".json")
        if source.exists():
            shutil.copy2(source, history / source.name)
    for name in REPORT_NAMES:
        write_report(directory, name, {"status": "UNVERIFIED", "reason": "Current run has not completed this measurement."})
    initial_digest = source_digest()
    code = run_test_reports(directory)
    with tempfile.TemporaryDirectory(prefix="kontext-report-") as temporary:
        data = Path(temporary)
        for name in ("raw", "chunks"):
            shutil.copytree(ROOT / "data" / name, data / name)
        os.environ.update({
            "DATA_DIR": str(data), "RAW_DATA_DIR": str(data / "raw"),
            "CHUNKS_DIR": str(data / "chunks"), "QDRANT_STORAGE_DIR": str(data / "vectors"),
            "AUDIT_LOG_PATH": str(data / "audit.jsonl"),
            "DATABASE_URL": "sqlite:///" + (data / "records.db").as_posix(),
            "API_KEYS": "{}", "LANGFUSE_ENABLED": "false",
        })
        run_retrieval_reports(directory)
        from app.evaluation.source_fidelity import evaluate_source_fidelity
        fidelity = evaluate_source_fidelity()
        write_report(directory, "citation_accuracy", fidelity)
        if fidelity["status"] != "PASS":
            code = 1
        from app.agent import nodes
        if nodes._hybrid_retriever is not None:
            nodes._hybrid_retriever.dense.client.close()
        from app.db.session import engine
        engine.dispose()
    final_digest = source_digest()
    unchanged = final_digest == initial_digest
    if not unchanged:
        code = 1
    write_report(directory, "run_manifest", {"status": "PASS" if code == 0 else "FAIL",
        "source_sha256": final_digest, "source_unchanged_during_run": unchanged,
        "source_scope": "All app/test/script Python files, requirements, curated/chunk/official JSON corpora and frozen evaluation inputs. Docker files are verified by the separate Docker report.",
        "python": sys.version, "deployment_status": "UNVERIFIED",
        "official_sdk_stdio": json.loads((directory / "mcp_sdk_interoperability.json").read_text(encoding="utf-8"))["status"],
        "external_desktop_hosts": "UNVERIFIED", "semantic_entailment": "UNVERIFIED"})
    print("Reports written to", directory)
    return code

if __name__ == "__main__":
    raise SystemExit(main())
