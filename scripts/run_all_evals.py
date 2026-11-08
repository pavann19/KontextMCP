"""Standalone executable script for running the evaluation benchmark."""

import sys
from app.evaluation.run_benchmark import run_all_evaluations

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    run_all_evaluations(save_reports=True)

