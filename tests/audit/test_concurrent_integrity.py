"""Concurrent audit logging, thread safety, and external checkpoint verification tests (P2 - Section 9)."""

import pytest
import concurrent.futures
from app.core.audit import AuditLogger

def test_concurrent_audit_logging_maintains_unbroken_chain():
    """Simulates 20 concurrent threads writing audit logs simultaneously."""
    num_threads = 20

    def write_log(idx: int):
        return AuditLogger.log_event(
            user_id=f"concurrent_user_{idx}",
            user_role="developer",
            action=f"CONCURRENT_ACTION_{idx}",
            status="EXECUTED",
            details=f"Concurrent thread execution log entry #{idx}"
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(write_log, i) for i in range(num_threads)]
        results = [f.result() for f in futures]

    assert len(results) == num_threads

    # Verify that the entire chain remains cryptographically valid with 0 broken links
    is_valid, count, err = AuditLogger.verify_integrity()
    assert is_valid is True, f"Audit integrity failed after concurrent execution: {err}"
    assert count >= num_threads

def test_hmac_signed_checkpoint_creation_and_verification():
    """Tests creation and verification of HMAC-SHA256 audit checkpoints."""
    checkpoint = AuditLogger.create_checkpoint()
    assert checkpoint.checkpoint_id.startswith("chk-")
    assert checkpoint.record_count > 0
    assert len(checkpoint.signature) == 64  # SHA-256 hex string

    # Verify checkpoint ledger
    is_valid, err = AuditLogger.verify_checkpoints()
    assert is_valid is True, f"Checkpoint verification failed: {err}"

def test_forged_checkpoint_key_rejection():
    """Verifies that verifying checkpoints with an incorrect key fails."""
    is_valid, err = AuditLogger.verify_checkpoints(secret_key="wrong-forged-key-999")
    assert is_valid is False
    assert "forgery detected" in err.lower()

