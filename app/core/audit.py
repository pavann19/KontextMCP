"""Tamper-evident audit logger with cryptographic hash chaining and external checkpoints (P6.9).

Maintains a secure, append-only, thread-safe, verifiable audit trail for all user interactions,
tool executions, permission denials, and security guardrail decisions.
Supports periodic HMAC-SHA256 external checkpointing to establish trust boundaries.
"""

import json
import hmac
import hashlib
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from app.config import settings
from app.db.session import get_db_context
from app.db.models import AuditLogRecord
from filelock import FileLock
from app.core.pii_guard import pii_guard

GENESIS_HASH = "0" * 64


class AuditEntry(BaseModel):
    event_id: Optional[str] = None
    id: Optional[int] = None
    trace_id: str
    timestamp: str
    user_id: str
    user_role: str
    action: str
    target_resource: Optional[str] = None
    status: str  # AUTHORIZED, PERMISSION_DENIED, EXECUTED, ERROR, BLOCKED_SECURITY
    details: str
    prev_hash: str
    record_hash: str

class AuditCheckpoint(BaseModel):
    checkpoint_id: str
    record_count: int
    last_record_hash: str
    timestamp: str
    signature: str

class AuditLogger:
    """Manages append-only JSONL audit streams and database records with SHA-256 chaining."""

    _last_hash: str = GENESIS_HASH
    _is_initialized: bool = False
    _lock: threading.RLock = threading.RLock()

    @classmethod
    def _initialize_last_hash(cls) -> None:
        """Finds the last hash from disk or database to ensure unbroken chaining."""
        cls._last_hash = GENESIS_HASH
        log_path = settings.AUDIT_LOG_PATH
        if log_path.exists():
            valid, _, error = cls.verify_integrity()
            if not valid:
                raise ValueError(f"Refusing to append to invalid audit log: {error}")
            # JSONL uses physical newlines; Unicode text separators stay inside strings.
            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").split("\n") if line.strip()]
            if records:
                cls._last_hash = records[-1]["record_hash"]
        cls._is_initialized = True

    @classmethod
    def compute_hash(cls, prev_hash: str, payload_data: Dict[str, Any]) -> str:
        """Computes deterministic SHA-256 hash over previous hash and canonical JSON payload."""
        canonical_json = json.dumps(payload_data, sort_keys=True, ensure_ascii=False)
        hasher = hashlib.sha256()
        hasher.update(prev_hash.encode("utf-8"))
        hasher.update(canonical_json.encode("utf-8"))
        return hasher.hexdigest()

    @classmethod
    def mask_sensitive_payload(cls, text: str) -> str:
        """Redacts sensitive credentials, passwords, tokens, and API keys before logging."""
        if not text:
            return ""
        import re
        masked = re.sub(r"(?i)\b(?:key|api[_-]?key|token|bearer|secret|password|passwd|pwd)\s*[:=]\s*['\"]?[A-Za-z0-9_\-\.]{8,}['\"]?", "[REDACTED_CREDENTIAL]", text)
        return masked

    @classmethod
    def log_event(
        cls,
        user_id: str,
        user_role: str,
        action: str,
        status: str,
        details: str,
        target_resource: Optional[str] = None,
        trace_id: Optional[str] = None,
        event_id: Optional[str] = None
    ) -> AuditEntry:
        """Records an immutable audit event in both JSONL and relational database with thread safety."""
        settings.AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with cls._lock, FileLock(str(settings.AUDIT_LOG_PATH) + ".writer.lock", timeout=30):
            # Refresh under an interprocess lock; another worker may have appended.
            cls._initialize_last_hash()

            if event_id:
                for line in settings.AUDIT_LOG_PATH.read_text(encoding="utf-8").split("\n") if settings.AUDIT_LOG_PATH.exists() else []:
                    if not line.strip():
                        continue
                    prior = json.loads(line)
                    if prior.get("event_id") == event_id:
                        if (prior["user_id"], prior["user_role"], prior["action"], prior["status"], prior["target_resource"], prior["details"]) != (user_id, user_role, action, status, target_resource, cls.mask_sensitive_payload(pii_guard.mask(details).clean_text)):
                            raise ValueError("Audit event ID reused with different payload")
                        return AuditEntry(**prior)
            t_now = datetime.now(timezone.utc).isoformat()
            t_id = trace_id or f"trc-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:17]}"

            sanitized_details = cls.mask_sensitive_payload(pii_guard.mask(details).clean_text)

            payload = {
                "trace_id": t_id,
                "timestamp": t_now,
                "user_id": user_id,
                "user_role": user_role,
                "action": action,
                "target_resource": target_resource or "none",
                "status": status,
                "details": sanitized_details
            }

            if event_id:
                payload["event_id"] = event_id
            prev_hash = cls._last_hash
            record_hash = cls.compute_hash(prev_hash, payload)

            entry = AuditEntry(
                event_id=event_id,
                trace_id=t_id,
                timestamp=t_now,
                user_id=user_id,
                user_role=user_role,
                action=action,
                target_resource=target_resource,
                status=status,
                details=sanitized_details,
                prev_hash=prev_hash,
                record_hash=record_hash
            )

            # 1. Append to JSONL file
            log_path = settings.AUDIT_LOG_PATH
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.model_dump(), ensure_ascii=False) + "\n")
                f.flush()
                import os
                os.fsync(f.fileno())
            cls._last_hash = record_hash

            # 2. Persist to database table
            try:
                with get_db_context() as session:
                    db_record = AuditLogRecord(
                        trace_id=entry.trace_id,
                        timestamp=datetime.fromisoformat(entry.timestamp),
                        user_id=entry.user_id,
                        user_role=entry.user_role,
                        action=entry.action,
                        target_resource=entry.target_resource,
                        status=entry.status,
                        details=entry.details,
                        prev_hash=entry.prev_hash,
                        record_hash=entry.record_hash
                    )
                    session.add(db_record)
                    session.commit()
                    entry.id = db_record.id
            except Exception:
                pass

            return entry

    @classmethod
    def verify_integrity(cls) -> Tuple[bool, int, Optional[str]]:
        """Verifies the unbroken cryptographic chain of all records in the audit log.
        
        Returns (is_valid, record_count, error_description).
        """
        with cls._lock:
            log_path = settings.AUDIT_LOG_PATH
            if not log_path.exists():
                return False, 0, "Audit log missing; integrity cannot be established."

            expected_prev_hash = GENESIS_HASH
            count = 0

            with open(log_path, "r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    count += 1
                    try:
                        record = AuditEntry(**json.loads(line)).model_dump()
                    except (ValueError, TypeError) as exc:
                        return False, count, f"Malformed audit record at line {line_no}: {exc}"
                    actual_prev_hash = record.get("prev_hash")
                    actual_record_hash = record.get("record_hash")

                    # Verify previous hash link
                    if actual_prev_hash != expected_prev_hash:
                        return False, count, (
                            f"Audit chain broken at line {line_no}! "
                            f"Expected prev_hash '{expected_prev_hash}', found '{actual_prev_hash}'."
                        )

                    # Recompute hash
                    payload = {
                        "trace_id": record["trace_id"],
                        "timestamp": record["timestamp"],
                        "user_id": record["user_id"],
                        "user_role": record["user_role"],
                        "action": record["action"],
                        "target_resource": record.get("target_resource") or "none",
                        "status": record["status"],
                        "details": record["details"]
                    }
                    if record.get("event_id"):
                        payload["event_id"] = record["event_id"]
                    recomputed = cls.compute_hash(actual_prev_hash, payload)
                    if recomputed != actual_record_hash:
                        return False, count, (
                            f"Tampered record at line {line_no}! "
                            f"Hash mismatch: recomputed '{recomputed}' != recorded '{actual_record_hash}'."
                        )

                    expected_prev_hash = actual_record_hash

            return True, count, None

    @classmethod
    def create_checkpoint(cls, secret_key: Optional[str] = None) -> AuditCheckpoint:
        """Creates an externally signed HMAC-SHA256 checkpoint of the current audit state."""
        secret_key = secret_key or settings.AUDIT_CHECKPOINT_KEY
        if not secret_key or len(secret_key) < 32:
            raise ValueError("Configure AUDIT_CHECKPOINT_KEY with at least 32 characters.")
        with cls._lock, FileLock(str(settings.AUDIT_LOG_PATH) + ".writer.lock", timeout=30):
            is_valid, count, err = cls.verify_integrity()
            if not is_valid:
                raise ValueError(f"Cannot create checkpoint on corrupted audit chain: {err}")

            t_now = datetime.now(timezone.utc).isoformat()
            cp_id = f"chk-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            records = [json.loads(line) for line in settings.AUDIT_LOG_PATH.read_text(encoding="utf-8").split("\n") if line.strip()]
            last_hash = records[-1]["record_hash"] if records else GENESIS_HASH

            # Compute HMAC signature over count + last_hash + timestamp
            msg = f"{cp_id}:{count}:{last_hash}:{t_now}".encode("utf-8")
            signature = hmac.new(secret_key.encode("utf-8"), msg, hashlib.sha256).hexdigest()

            checkpoint = AuditCheckpoint(
                checkpoint_id=cp_id,
                record_count=count,
                last_record_hash=last_hash,
                timestamp=t_now,
                signature=signature
            )

            # Save checkpoint to disk
            cp_file = settings.DATA_DIR / "audit_checkpoints.json"
            cp_list = []
            if cp_file.exists():
                try:
                    with open(cp_file, "r", encoding="utf-8") as f:
                        cp_list = json.load(f)
                except (ValueError, OSError) as exc:
                    raise ValueError("Refusing to replace malformed checkpoint ledger") from exc

            cp_list.append(checkpoint.model_dump())
            with open(cp_file, "w", encoding="utf-8") as f:
                json.dump(cp_list, f, indent=2)

            return checkpoint

    @classmethod
    def verify_checkpoints(cls, secret_key: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Verify signatures AND anchor each checkpoint to the current chain prefix.

        The checkpoint ledger must also be retained outside this writable directory
        to detect deletion of both the log and its local checkpoints.
        """
        secret_key = secret_key or settings.AUDIT_CHECKPOINT_KEY
        if not secret_key:
            return False, "Checkpoint verification unavailable: configure AUDIT_CHECKPOINT_KEY."
        with cls._lock:
            valid, _, error = cls.verify_integrity()
            if not valid:
                return False, error
            cp_file = settings.DATA_DIR / "audit_checkpoints.json"
            if not cp_file.exists():
                return False, "Checkpoint ledger missing; no trusted anchor available."
            try:
                checkpoints = json.loads(cp_file.read_text(encoding="utf-8"))
                if not isinstance(checkpoints, list) or not checkpoints:
                    return False, "Checkpoint ledger is empty or malformed."
                hashes = [GENESIS_HASH] + [json.loads(line)["record_hash"] for line in
                    settings.AUDIT_LOG_PATH.read_text(encoding="utf-8").split("\n") if line.strip()]
                for raw in checkpoints:
                    cp = AuditCheckpoint(**raw)
                    msg = f"{cp.checkpoint_id}:{cp.record_count}:{cp.last_record_hash}:{cp.timestamp}".encode()
                    signature = hmac.new(secret_key.encode(), msg, hashlib.sha256).hexdigest()
                    if not hmac.compare_digest(signature, cp.signature):
                        return False, f"Checkpoint signature forgery detected: {cp.checkpoint_id}"
                    if cp.record_count < 0 or cp.record_count >= len(hashes):
                        return False, "Audit log truncated before a checkpoint."
                    if hashes[cp.record_count] != cp.last_record_hash:
                        return False, "Audit log differs from checkpoint anchor."
            except (ValueError, TypeError, KeyError, OSError) as exc:
                return False, f"Malformed checkpoint or audit ledger: {exc}"
            return True, None

    @classmethod
    def query_logs(
        cls,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[AuditEntry]:
        """Queries recent audit entries with filtering."""
        with cls._lock:
            log_path = settings.AUDIT_LOG_PATH
            if not log_path.exists():
                return []

            entries: List[AuditEntry] = []
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    record = json.loads(line.strip())
                    if user_id and record.get("user_id") != user_id:
                        continue
                    if role and record.get("user_role") != role:
                        continue
                    if status and record.get("status") != status:
                        continue
                    entries.append(AuditEntry(**record))

            return list(reversed(entries))[:limit]
