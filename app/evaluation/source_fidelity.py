"""Measure exact source fidelity of actual guarded answers over fixed local queries.

No judge model, semantic entailment metric or official-source claim is involved.
"""
from app.agent.graph import run_agent_query
from app.core.grounding import verify_excerpts
from app.core.audit import AuditLogger
from app.core.pii_guard import pii_guard
from app.evaluation.benchmark_dataset import generate_benchmark_dataset
from app.evaluation.evaluator import BenchmarkEvaluator

UNSUPPORTED = [
    ("What does Article 112 require?", "en"),
    ("What does Article 111 require?", "en"),
    ("What does Article 100 require?", "en"),
    ("What does Article 0 require?", "en"),
    ("What does Article -1 require?", "en"),
    ("What does Article 150 require?", "en"),
    ("What does Annex IX require?", "en"),
    ("Was verlangt Artikel 112?", "de"),
    ("Was verlangt Anhang IX?", "de"),
    ("Which stocks should I buy?", "en"),
]


def evaluate_source_fidelity():
    from app.agent import nodes
    nodes.get_retrieval_engine()
    trusted = {c.chunk_id: c.model_dump() for c in nodes._cached_chunks}
    rows = []
    for item in generate_benchmark_dataset():
        if item.language == "tool":
            continue
        state = run_agent_query(item.query)
        if state.grounding_status == "SOURCE_VERIFIED":
            valid, error = verify_excerpts(state.final_answer, state.citations, trusted,
                state.target_language or "en", sanitize=lambda text: AuditLogger.mask_sensitive_payload(pii_guard.mask(text).clean_text))
        else:
            valid, error = None, state.grounding_error
        relevant = any(BenchmarkEvaluator._matches_expected_article(c["article_id"], item.expected_article_id) for c in state.citations)
        rows.append({"query_id": item.query_id, "language": item.language,
                     "grounding_status": state.grounding_status, "source_fidelity_valid": valid,
                     "expected_article_in_returned_citations": relevant,
                     "citation_count": len(state.citations), "error": error})
    unsupported = []
    for query, language in UNSUPPORTED:
        state = run_agent_query(query, target_language=language)
        abstained = not state.citations and "[[source:" not in state.final_answer and state.grounding_status == "NOT_APPLICABLE"
        unsupported.append({"query": query, "abstained": abstained, "answer": state.final_answer})
    answered = [r for r in rows if r["source_fidelity_valid"] is not None]
    rejected = sum(r["grounding_status"] == "REJECTED" for r in rows)
    failures = sum(r["source_fidelity_valid"] is False for r in answered)
    return {"status": "PASS" if answered and not failures and not rejected and all(r["abstained"] for r in unsupported) else "FAIL",
            "evaluation_queries": len(rows), "answers_with_excerpts": len(answered),
            "not_applicable_or_abstained": len(rows)-len(answered)-rejected, "guard_rejections": rejected,
            "source_fidelity_failures": failures,
            "source_fidelity_rate_among_excerpt_answers": sum(r["source_fidelity_valid"] for r in answered)/len(answered) if answered else None,
            "expected_article_returned_rate_all_queries": sum(r["expected_article_in_returned_citations"] for r in rows)/len(rows),
            "unsupported_fixed_cases": len(unsupported), "unsupported_cases_abstained": sum(r["abstained"] for r in unsupported),
            "semantic_entailment": "UNVERIFIED", "official_source_equivalence": "UNVERIFIED",
            "limitation": "Exact excerpts and metadata checked against the same local curated corpus, after configured redaction. Generated fixed queries, no holdout or independent legal correctness assessment. Relevance is reported separately from source fidelity.",
            "queries": rows, "unsupported_results": unsupported}
