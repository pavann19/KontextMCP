"""Master benchmark runner executing P6.11 and P6.12 evaluations."""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any
from app.config import settings
from app.evaluation.benchmark_dataset import generate_benchmark_dataset
from app.evaluation.evaluator import BenchmarkEvaluator
from app.evaluation.red_teaming import RedTeamHarness

def run_all_evaluations(save_reports: bool = True) -> Dict[str, Any]:
    """Runs the 250-query benchmark and the security red-teaming test suite."""
    print("=" * 70, flush=True)
    print("🚀 STARTING COMPREHENSIVE BENCHMARK & RED-TEAMING EVALUATION", flush=True)
    print("=" * 70, flush=True)

    # 1. Generate & Run 250-Query Retrieval Benchmark
    print("\n--- [P6.11] Running 250-Query Bilingual Evaluation Benchmark ---", flush=True)
    dataset = [q for q in generate_benchmark_dataset() if q.language != "tool"]
    t_start = time.time()
    metrics = BenchmarkEvaluator.run_benchmark(dataset=dataset, verbose=True)
    bench_duration = round(time.time() - t_start, 2)
    print(f"Benchmark completed in {bench_duration}s. Hit@1: {metrics.hit_at_1*100:.1f}%, Hit@3: {metrics.hit_at_3*100:.1f}%, MRR: {metrics.mrr:.4f}", flush=True)

    # 2. Run Red-Teaming Security Suite
    print("\n--- [P6.12] Running Security Red-Teaming & Threat Simulation ---", flush=True)
    red_results, pass_rate = RedTeamHarness.run_tests(verbose=True)
    print(f"Red-teaming completed. Defense Success Rate: {pass_rate*100:.1f}%", flush=True)

    # 3. Generate Reports
    bench_md = BenchmarkEvaluator.generate_markdown_report(metrics)
    red_md = RedTeamHarness.generate_red_team_report(red_results, pass_rate)
    full_report_md = f"{bench_md}\n\n---\n\n{red_md}"

    output_dir = settings.DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if save_reports:
        report_path = output_dir / "benchmark_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(full_report_md)

        results_json_path = output_dir / "benchmark_results.json"
        with open(results_json_path, "w", encoding="utf-8") as f:
            json.dump({
                "benchmark_metrics": metrics.model_dump(),
                "red_teaming": {
                    "total_tests": len(red_results),
                    "defense_pass_rate": pass_rate,
                    "results": [r.model_dump() for r in red_results]
                },
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }, f, indent=2, ensure_ascii=False)

        print(f"\n✅ All reports successfully saved to:\n- {report_path}\n- {results_json_path}", flush=True)

    return {
        "metrics": metrics.model_dump(),
        "red_teaming_pass_rate": pass_rate,
        "full_report_md": full_report_md
    }

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run_all_evaluations()
