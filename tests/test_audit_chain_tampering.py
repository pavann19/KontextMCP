"""Tests for audit chain cryptographic integrity and tampering detection (P6.9)."""

import json
import pytest
from pathlib import Path
from app.config import settings
from app.core.audit import AuditLogger, GENESIS_HASH

@pytest.fixture
def temp_audit_file(tmp_path):
    """Creates a temporary test audit log with 5 valid hash-chained entries."""
    audit_file = tmp_path / "test_audit.jsonl"
    old_path = settings.AUDIT_LOG_PATH
    settings.AUDIT_LOG_PATH = audit_file

    AuditLogger._last_hash = GENESIS_HASH
    AuditLogger._is_initialized = True

    # Generate 5 chained records
    for i in range(1, 6):
        AuditLogger.log_event(
            user_id=f"user_{i}",
            user_role="auditor",
            action=f"ACTION_{i}",
            status="EXECUTED" if i % 2 == 0 else "PERMISSION_DENIED",
            details=f"Event details number {i}"
        )

    yield audit_file

    # Restore settings
    settings.AUDIT_LOG_PATH = old_path
    AuditLogger._is_initialized = False

def test_unaltered_audit_chain_is_valid(temp_audit_file):
    """Verifies that an unaltered audit log returns valid=True."""
    valid, count, err = AuditLogger.verify_integrity()
    assert valid is True
    assert count == 5
    assert err is None

def test_detect_payload_tampering(temp_audit_file):
    """Verifies that altering a record's data (e.g. changing PERMISSION_DENIED to AUTHORIZED) is detected."""
    lines = []
    with open(temp_audit_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Tamper with record 3: change status
    rec3 = json.loads(lines[2])
    rec3["status"] = "AUTHORIZED"  # Maliciously alter status without recalculating hash
    lines[2] = json.dumps(rec3)

    with open(temp_audit_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    valid, count, err = AuditLogger.verify_integrity()
    assert valid is False
    assert count == 3
    assert "Tampered record at line 3" in err
    assert "Hash mismatch" in err

def test_detect_broken_chain_prev_hash(temp_audit_file):
    """Verifies that altering a prev_hash pointer is immediately flagged."""
    lines = []
    with open(temp_audit_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Tamper with record 4's prev_hash
    rec4 = json.loads(lines[3])
    rec4["prev_hash"] = "f" * 64
    lines[3] = json.dumps(rec4)

    with open(temp_audit_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    valid, count, err = AuditLogger.verify_integrity()
    assert valid is False
    assert count == 4
    assert "Audit chain broken at line 4" in err

def test_detect_deleted_record(temp_audit_file):
    """Verifies that deleting a record from the middle of the chain breaks the chain."""
    lines = []
    with open(temp_audit_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Delete record 2 (lines[1])
    del lines[1]

    with open(temp_audit_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    valid, count, err = AuditLogger.verify_integrity()
    assert valid is False
    assert "Audit chain broken" in err

