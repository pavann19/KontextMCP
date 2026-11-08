import hashlib,json
from pathlib import Path
import pytest
from scripts.import_official_corpus import parse_html
from app.ingestion.chunker import LegalDocumentChunker


def test_official_snapshots_reparse_and_cover_full_structure():
    root=Path(__file__).resolve().parents[2]
    report_path=root/"artifacts/reports/official_source_comparison.json"
    if not report_path.exists():pytest.skip("Run official importer to create snapshots")
    report=json.loads(report_path.read_text(encoding="utf-8"))
    for language,data in report["languages"].items():
        snapshot=root/Path(data["snapshot"].replace("\\","/"))
        assert hashlib.sha256(snapshot.read_bytes()).hexdigest()==data["html_sha256"]
        docs=parse_html(snapshot.read_text(encoding="utf-8"),language,data["url"])
        assert sum(d["type"]=="article" for d in docs)==113
        assert sum(d["type"]=="annex" for d in docs)==13
        chunks=LegalDocumentChunker(max_tokens=300).chunk_all(docs)
        assert {c.doc_id for c in chunks}=={d["doc_id"] for d in docs}
        assert max(len(c.text) for c in chunks)<2000


def test_named_official_provision_survives_lexical_candidate_miss(monkeypatch):
    from app.agent import nodes
    from app.agent.state import AgentState
    from app.ingestion.pipeline import IngestionPipeline
    from app.config import settings
    from app.retrieval.reranker import LegalCrossReranker
    from app.mcp.permissions import UserContext
    from types import SimpleNamespace
    # Parse the actual publication; the simulated candidate miss must not cause
    # an abstention when a provision exists in the trusted corpus.
    chunks = IngestionPipeline(raw_dir=settings.OFFICIAL_RAW_DATA_DIR, chunks_dir=settings.DATA_DIR / "official-regression").run()
    monkeypatch.setattr(nodes, "_cached_chunks", chunks)
    monkeypatch.setattr(nodes, "get_retrieval_engine", lambda: (
        SimpleNamespace(search=lambda *args, **kwargs: []), LegalCrossReranker()))
    state = AgentState(trace_id="official-regression", original_query="What does Article 9 require?",
        sanitized_query="What does Article 9 require?", target_language="en",
        user_context=UserContext(username="public", role="public_viewer", department="public"))
    result = nodes.retrieval_node(state)
    assert result["retrieved_chunks"]
    assert all(c["article_id"] == "Article 9" for c in result["retrieved_chunks"])
    assert all(c["language"] == "en" for c in result["retrieved_chunks"])
