"""Always isolate database, audit, telemetry and vector state before app imports."""
import os
import shutil
import tempfile
from pathlib import Path
import pytest

_TEST_STORAGE = tempfile.TemporaryDirectory(prefix="kontext-tests-")
_TEST_ROOT = Path(_TEST_STORAGE.name)
_REPO = Path(__file__).resolve().parents[1]
for name in ("raw", "chunks"):
    source = _REPO / "data" / name
    if source.exists():
        shutil.copytree(source, _TEST_ROOT / name)
for key, value in {
    "ENVIRONMENT": "test",
    "DATABASE_SCHEMA_MODE": "create",
    "HTTP_ALLOWED_HOSTS": '["localhost","127.0.0.1","testserver"]',
    "DATA_DIR": str(_TEST_ROOT),
    "RAW_DATA_DIR": str(_TEST_ROOT / "raw"),
    "CHUNKS_DIR": str(_TEST_ROOT / "chunks"),
    "QDRANT_STORAGE_DIR": str(_TEST_ROOT / "qdrant"),
    "QDRANT_PREFER_LOCAL": "false",
    "QDRANT_HOST": "",
    "AUDIT_LOG_PATH": str(_TEST_ROOT / "audit.jsonl"),
    "DATABASE_URL": "sqlite:///" + (_TEST_ROOT / "test.db").as_posix(),
    "AUDIT_CHECKPOINT_KEY": "test-only-checkpoint-key-with-32-characters",
    "API_KEYS": "{}",
    "CORPUS_VARIANT": "curated",
    "SYNTHESIS_MODE": "extractive",
    "LANGFUSE_ENABLED": "false",
}.items():
    os.environ[key] = value

@pytest.fixture(scope="session", autouse=True)
def isolated_storage():
    from app.db.seed_data import seed_database
    from app.core.audit import AuditLogger
    seed_database()
    AuditLogger.log_event("test", "auditor", "TEST_SETUP", "EXECUTED", "Isolated test setup")
    AuditLogger.create_checkpoint()
    yield
    from app.agent import nodes
    if nodes._hybrid_retriever is not None:
        nodes._hybrid_retriever.dense.client.close()
        nodes._hybrid_retriever = None
        nodes._reranker = None
    from app.db.session import engine
    engine.dispose()
    from app.agent import nodes
    from app.api import routes_search
    for retriever in (nodes._hybrid_retriever, routes_search._hybrid):
        if retriever:
            retriever.dense.client.close()
    _TEST_STORAGE.cleanup()
