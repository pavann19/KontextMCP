"""Quantitative Metrics Evaluator for Retrieval and Answer Generation (P6.11)."""

import math
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pydantic import BaseModel, Field

from app.evaluation.benchmark_dataset import BenchmarkItem, generate_benchmark_dataset
from app.agent.graph import run_agent_query
from app.mcp.permissions import UserContext

class EvaluationMetrics(BaseModel):
    total_queries: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    mrr: float
    precision_at_3: float
    recall_at_3: float
    ndcg_at_3: float
    keyword_coverage: float
    mean_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    category_metrics: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    language_metrics: Dict[str, Dict[str, float]] = Field(default_factory=dict)

class BenchmarkEvaluator:
    """Executes benchmark queries and computes IR and generation metrics."""

    @staticmethod
    def _matches_expected_article(retrieved_article_id: str, expected_article_id: str) -> bool:
        """Checks if retrieved article corresponds to expected legal citation."""
        import re
        def canonical(value):
            value = value.lower().strip()
            match = re.fullmatch(r"(?:article|artikel|art\.?)\s*(\d+)", value)
            if match:
                return ("article", int(match.group(1)))
            match = re.fullmatch(r"(?:annex|anhang)\s*([ivxlcdm]+|\d+)", value)
            if match:
                roman = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
                token = match.group(1)
                number = int(token) if token.isdigit() else sum(
                    -roman[c] if i + 1 < len(token) and roman[c] < roman[token[i+1]] else roman[c]
                    for i, c in enumerate(token))
                return ("annex", number)
            return ("other", value)
        return canonical(retrieved_article_id) == canonical(expected_article_id)

    @classmethod
    def evaluate_item(
        cls,
        item: BenchmarkItem,
        user: Optional[UserContext] = None
    ) -> Dict[str, Any]:
        """Runs a single benchmark item and calculates item-level metrics."""
        t0 = time.time()
        user_ctx = user or UserContext(username="alice_compliance", role="compliance_officer", department="legal_compliance", clearance_level=4)
        state = run_agent_query(item.query, user=user_ctx)
        latency = (time.time() - t0) * 1000

        # Extract retrieved article IDs from citations or chunks
        retrieved_ids = []
        for chunk in state.retrieved_chunks:
            article = chunk.get("article_id", "")
            if not any(cls._matches_expected_article(article, seen) for seen in retrieved_ids):
                retrieved_ids.append(article)
        if not retrieved_ids and state.tool_results:
            # For tool queries, check if target was queried
            first_tool = state.tool_results[0].get("result", "")
            if item.expected_article_id.lower() in first_tool.lower():
                retrieved_ids = [item.expected_article_id]

        # Calculate Rank for MRR
        rank = 0
        hit_1 = 0.0
        hit_3 = 0.0
        hit_5 = 0.0

        for idx, art_id in enumerate(retrieved_ids[:5], start=1):
            if cls._matches_expected_article(art_id, item.expected_article_id):
                if rank == 0:
                    rank = idx
                if idx == 1:
                    hit_1 = 1.0
                if idx <= 3:
                    hit_3 = 1.0
                if idx <= 5:
                    hit_5 = 1.0

        reciprocal_rank = 1.0 / rank if rank > 0 else 0.0

        # DCG@3
        dcg = 0.0
        idcg = 1.0  # Perfect case: relevant item at rank 1
        for idx, art_id in enumerate(retrieved_ids[:3], start=1):
            rel = 1.0 if cls._matches_expected_article(art_id, item.expected_article_id) else 0.0
            dcg += rel / math.log2(idx + 1)
        ndcg = dcg / idcg

        # Keyword coverage in final answer
        ans_lower = state.final_answer.lower()
        matched_kws = sum(1 for kw in item.expected_keywords if kw.lower() in ans_lower)
        kw_cov = matched_kws / len(item.expected_keywords) if item.expected_keywords else 1.0

        return {
            "query_id": item.query_id,
            "language": item.language,
            "category": item.category,
            "latency_ms": latency,
            "hit_1": hit_1,
            "hit_3": hit_3,
            "hit_5": hit_5,
            "mrr": reciprocal_rank,
            "ndcg_3": ndcg,
            "keyword_coverage": kw_cov,
            "retrieved_count": len(retrieved_ids)
        }

    @classmethod
    def run_benchmark(
        cls,
        dataset: Optional[List[BenchmarkItem]] = None,
        max_samples: Optional[int] = None,
        verbose: bool = True
    ) -> EvaluationMetrics:
        """Runs the entire benchmark dataset or a subset and computes aggregate metrics."""
        items = dataset if dataset is not None else [q for q in generate_benchmark_dataset() if q.language != "tool"]
        if not items:
            raise ValueError("Benchmark dataset must not be empty.")
        if max_samples and max_samples < len(items):
            items = items[:max_samples]

        results = []
        for i, item in enumerate(items, start=1):
            res = cls.evaluate_item(item)
            results.append(res)
            if verbose and (i % 25 == 0 or i == len(items)):
                print(f"Processed {i}/{len(items)} queries... Current Hit@3: {round(np.mean([r['hit_3'] for r in results]), 3)}", flush=True)

        # Aggregate Metrics
        hit_1 = float(np.mean([r["hit_1"] for r in results]))
        hit_3 = float(np.mean([r["hit_3"] for r in results]))
        hit_5 = float(np.mean([r["hit_5"] for r in results]))
        mrr = float(np.mean([r["mrr"] for r in results]))
        ndcg = float(np.mean([r["ndcg_3"] for r in results]))
        kw_cov = float(np.mean([r["keyword_coverage"] for r in results]))
        latencies = [r["latency_ms"] for r in results]

        # Breakdown by language
        lang_breakdown: Dict[str, Dict[str, float]] = {}
        for l in ["en", "de", "cross", "tool"]:
            subset = [r for r in results if r["language"] == l]
            if subset:
                lang_breakdown[l] = {
                    "count": len(subset),
                    "hit_at_1": float(np.mean([r["hit_1"] for r in subset])),
                    "hit_at_3": float(np.mean([r["hit_3"] for r in subset])),
                    "mrr": float(np.mean([r["mrr"] for r in subset])),
                    "keyword_coverage": float(np.mean([r["keyword_coverage"] for r in subset])),
                    "avg_latency_ms": float(np.mean([r["latency_ms"] for r in subset]))
                }

        metrics = EvaluationMetrics(
            total_queries=len(results),
            hit_at_1=round(hit_1, 4),
            hit_at_3=round(hit_3, 4),
            hit_at_5=round(hit_5, 4),
            mrr=round(mrr, 4),
            precision_at_3=round(hit_3 / 3.0, 4),
            recall_at_3=round(hit_3, 4),
            ndcg_at_3=round(ndcg, 4),
            keyword_coverage=round(kw_cov, 4),
            mean_latency_ms=round(float(np.mean(latencies)), 2),
            p50_latency_ms=round(float(np.percentile(latencies, 50)), 2),
            p95_latency_ms=round(float(np.percentile(latencies, 95)), 2),
            language_metrics=lang_breakdown
        )
        return metrics

    @classmethod
    def generate_markdown_report(cls, metrics: EvaluationMetrics) -> str:
        """Generates a professional Markdown evaluation report with tables."""
        rows = [
            "# Local agent retrieval evaluation", "",
            f"Queries evaluated: {metrics.total_queries}", "",
            "Fixed generated questions over a curated corpus; no independent holdout. These measurements do not establish legal accuracy or production capacity.", "",
            "| Metric | Measured value |", "| --- | --- |",
            f"| Hit@1 | {metrics.hit_at_1:.4f} |",
            f"| Hit@3 | {metrics.hit_at_3:.4f} |",
            f"| Hit@5 | {metrics.hit_at_5:.4f} |",
            f"| MRR | {metrics.mrr:.4f} |",
            f"| NDCG@3 | {metrics.ndcg_at_3:.4f} |",
            f"| Mean latency | {metrics.mean_latency_ms:.2f} ms |",
            f"| P95 latency | {metrics.p95_latency_ms:.2f} ms |", "",
            "Chat returns at most three chunks, so Hit@5 is bounded by that configuration. Article matches do not measure citation entailment."
        ]
        return "\n".join(rows)
