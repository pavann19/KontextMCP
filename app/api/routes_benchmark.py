"""Evaluation benchmark and security red-teaming API routes (P6.11 & P6.12)."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from app.config import settings
from app.core.security import resolve_user_context
from app.mcp.permissions import UserContext
from app.evaluation.evaluator import BenchmarkEvaluator, EvaluationMetrics
from app.evaluation.red_teaming import RedTeamHarness
from app.evaluation.run_benchmark import run_all_evaluations

router = APIRouter(prefix="/benchmark", tags=["Evaluation & Red-Teaming"])

class BenchmarkRunResponse(BaseModel):
    status: str
    benchmark_metrics: EvaluationMetrics
    red_teaming_pass_rate: float
    total_red_team_tests: int

@router.post("/run", response_model=BenchmarkRunResponse)
def execute_benchmark_suite(
    sample_limit: Optional[int] = Query(None, description="Optional cap on benchmark query count for quick testing."),
    user: UserContext = Depends(resolve_user_context)
):
    """Triggers the 250-query retrieval benchmark and 15-vector security red-teaming suite."""
    if user.clearance_level < 3:
        raise HTTPException(
            status_code=403,
            detail="Benchmark execution restricted to Auditor or Compliance Officer."
        )
    if settings.ENVIRONMENT == "production":
        raise HTTPException(403, "Run evaluations offline; production requests cannot start benchmark workloads.")

    # 1. Run Benchmark
    metrics = BenchmarkEvaluator.run_benchmark(max_samples=sample_limit, verbose=False)
    
    # 2. Run Red-Teaming
    red_results, pass_rate = RedTeamHarness.run_tests(verbose=False)

    return BenchmarkRunResponse(
        status="EVALUATION_COMPLETED",
        benchmark_metrics=metrics,
        red_teaming_pass_rate=round(pass_rate, 4),
        total_red_team_tests=len(red_results)
    )

@router.get("/report")
def get_latest_benchmark_report(
    user: UserContext = Depends(resolve_user_context)
):
    """Retrieves the latest generated Markdown evaluation and security report."""
    if user.clearance_level < 3:
        raise HTTPException(403, "Benchmark reports require auditor clearance.")
    report_file = settings.DATA_DIR / "benchmark_report.md"
    if not report_file.exists():
        raise HTTPException(404, "No saved benchmark report; run the offline evaluator explicitly.")

    with open(report_file, "r", encoding="utf-8") as f:
        content = f.read()

    return {"report_markdown": content}

@router.get("/results")
def get_latest_benchmark_json(
    user: UserContext = Depends(resolve_user_context)
):
    """Retrieves the latest quantitative benchmark metrics in structured JSON."""
    if user.clearance_level < 3:
        raise HTTPException(403, "Benchmark results require auditor clearance.")
    results_file = settings.DATA_DIR / "benchmark_results.json"
    if not results_file.exists():
        raise HTTPException(404, "No saved benchmark results; run the offline evaluator explicitly.")

    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data

