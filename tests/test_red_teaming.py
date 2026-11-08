"""Tests for red-teaming security battery (P6.12)."""

import pytest
from app.evaluation.red_teaming import RedTeamHarness

def test_full_red_teaming_suite():
    results, pass_rate = RedTeamHarness.run_tests(verbose=False)
    assert len(results) == 15, "Expected 15 red-teaming test vectors"
    # Target 100% defense rate
    assert pass_rate == 1.0, [r.model_dump() for r in results if not r.passed]

