import json
import pytest
from app.config import settings
from app.core.audit import AuditLogger

@pytest.fixture
def ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "AUDIT_LOG_PATH", tmp_path / "audit.jsonl")
    monkeypatch.setattr(AuditLogger, "_is_initialized", False)
    for i in range(3):
        AuditLogger.log_event("test", "auditor", "TEST", "EXECUTED", str(i))
    AuditLogger.create_checkpoint()
    return settings.AUDIT_LOG_PATH


def test_truncation_is_detected_by_checkpoint(ledger):
    lines = ledger.read_text(encoding="utf-8").splitlines()
    ledger.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    assert AuditLogger.verify_integrity()[0]  # Remaining prefix is internally consistent.
    valid, error = AuditLogger.verify_checkpoints()
    assert not valid and "truncated" in error


def test_missing_log_and_malformed_record_fail_closed(ledger):
    ledger.unlink()
    assert not AuditLogger.verify_integrity()[0]
    assert not AuditLogger.verify_checkpoints()[0]
    ledger.write_text("not json\n", encoding="utf-8")
    assert not AuditLogger.verify_integrity()[0]
    with pytest.raises(ValueError, match="invalid audit"):
        AuditLogger.log_event("test", "auditor", "TEST", "EXECUTED", "no append")


def test_checkpoint_reads_tip_after_restart(ledger, monkeypatch):
    monkeypatch.setattr(AuditLogger, "_last_hash", "0" * 64)
    cp = AuditLogger.create_checkpoint()
    assert cp.last_record_hash == json.loads(ledger.read_text(encoding="utf-8").splitlines()[-1])["record_hash"]
    assert AuditLogger.verify_checkpoints()[0]


def test_rewritten_chain_is_rejected_by_anchor(ledger):
    records = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    previous = "0" * 64
    for record in records:
        record["details"] = "rewritten payload"
        payload = {k: record[k] for k in ("trace_id", "timestamp", "user_id", "user_role", "action", "target_resource", "status", "details")}
        payload["target_resource"] = payload["target_resource"] or "none"
        record["prev_hash"] = previous
        record["record_hash"] = AuditLogger.compute_hash(previous, payload)
        previous = record["record_hash"]
    ledger.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")
    assert AuditLogger.verify_integrity()[0]
    assert not AuditLogger.verify_checkpoints()[0]


def test_separate_process_writers_preserve_chain(ledger):
    import os
    import sys
    import subprocess
    from concurrent.futures import ThreadPoolExecutor
    environment = {**os.environ, "AUDIT_LOG_PATH": str(ledger), "DATA_DIR": str(ledger.parent)}
    script = "from app.core.audit import AuditLogger; [AuditLogger.log_event('worker','auditor','PROCESS','EXECUTED',str(i)) for i in range(5)]"
    def worker(_):
        result = subprocess.run([sys.executable, "-c", script], env=environment, capture_output=True, text=True, timeout=45)
        assert result.returncode == 0, result.stderr
    with ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(worker, range(3)))
    valid, count, error = AuditLogger.verify_integrity()
    assert valid, error
    assert count == 18
    assert AuditLogger.verify_checkpoints()[0]


@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029"])
def test_unicode_separators_do_not_split_jsonl_records(ledger, tmp_path, separator):
    from app.core.anchors import initialize, export_anchor, verify_anchor

    details = "Reviewed clause" + separator + "continued clause"
    event_id = "unicode-" + str(ord(separator))
    first = AuditLogger.log_event("test", "auditor", "UNICODE", "EXECUTED", details,
                                  event_id=event_id)
    repeated = AuditLogger.log_event("test", "auditor", "UNICODE", "EXECUTED", details,
                                     event_id=event_id)
    assert repeated.record_hash == first.record_hash
    AuditLogger.log_event("test", "auditor", "AFTER_UNICODE", "EXECUTED", "next")
    assert AuditLogger.verify_integrity()[0]
    checkpoint = AuditLogger.create_checkpoint()
    assert checkpoint.record_count == 5  # Three fixture entries plus two distinct writes.
    assert AuditLogger.verify_checkpoints()[0]
    directory = tmp_path.parent / (tmp_path.name + "-external")
    initialize(directory)
    anchor = export_anchor(directory)
    assert verify_anchor(anchor, directory / "trusted-public.key", ledger)
