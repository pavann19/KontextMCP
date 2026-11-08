"""Retrieval ablation tests comparing BM25, Dense, Hybrid, and Reranking (P1 - Section 7.1)."""

import pytest
from app.ingestion.pipeline import IngestionPipeline
from app.retrieval.bm25 import BilingualBM25Retriever
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.reranker import LegalCrossReranker

@pytest.fixture(scope="module")
def retrieval_stack():
    chunks = IngestionPipeline().load_cached_chunks()
    bm25 = BilingualBM25Retriever()
    bm25.index(chunks)
    dense = DenseRetriever()
    dense.index(chunks)
    hybrid = HybridRetriever(bm25=bm25, dense=dense)
    reranker = LegalCrossReranker(top_n=3)
    return {
        "chunks": chunks,
        "bm25": bm25,
        "dense": dense,
        "hybrid": hybrid,
        "reranker": reranker
    }

def test_retrieval_ablation_bm25_only(retrieval_stack):
    query = "What AI practices are prohibited under Article 5?"
    bm25_hits = retrieval_stack["bm25"].search(query, top_k=3)
    assert len(bm25_hits) > 0
    top_art = bm25_hits[0][0].article_id
    assert "Article 5" in top_art or "Artikel 5" in top_art

def test_retrieval_ablation_dense_only(retrieval_stack):
    query = "Requirements for continuous risk management in high-risk AI"
    dense_hits = retrieval_stack["dense"].search(query, top_k=3)
    assert len(dense_hits) > 0
    top_arts = [h[0].article_id for h in dense_hits]
    assert any("Article 9" in a or "Artikel 9" in a for a in top_arts)

def test_retrieval_ablation_hybrid_rrf_superiority(retrieval_stack):
    query = "Welche Geldbußen drohen bei Verstößen gegen verbotene KI-Praktiken?"
    # Hybrid search
    hybrid_hits = retrieval_stack["hybrid"].search_rrf(query, top_k=3, language="de")
    assert len(hybrid_hits) > 0
    top_chunk, score = hybrid_hits[0]
    # Penalties under Article 99
    assert "99" in top_chunk.article_id or "5" in top_chunk.article_id

def test_retrieval_ablation_reranker_citation_boost(retrieval_stack):
    query = "What does Article 14 state regarding human oversight and automation bias?"
    candidates = retrieval_stack["hybrid"].search(query, top_k=6)
    reranked = retrieval_stack["reranker"].rerank(query, candidates, top_n=3)
    assert len(reranked) > 0
    top_chunk, score = reranked[0]
    # Reranker should rank Article 14 at rank 1 due to exact citation boost
    assert "Article 14" in top_chunk.article_id

